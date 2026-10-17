"""Calcul du score et accès à la base des fiches d'audit.

La base est SQLite en local (fichier audits.db) ou Postgres en ligne : il suffit de
renseigner DATABASE_URL (variable d'environnement ou secret Streamlit).
"""

import os
from datetime import datetime

from sqlalchemy import (Column, Float, ForeignKey, Integer, MetaData, String, Table, Text,
                        create_engine, func, insert, inspect, select, text)

from rubriques import (COEF_CRITIQUE, EVALUATIONS, POINTS_MAX, RUBRIQUES,
                       SEUIL_A_AMELIORER, SEUIL_SATISFAISANT)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# --- Calcul du score (mêmes règles que les grilles Excel) -------------------

def coef(critique):
    return COEF_CRITIQUE if critique else 1


def resultat(score, nb_nc_critiques):
    if score is None:
        return None
    if nb_nc_critiques:
        return "Insuffisant (point critique NC)"
    if score >= SEUIL_SATISFAISANT:
        return "Satisfaisant"
    if score >= SEUIL_A_AMELIORER:
        return "À améliorer"
    return "Insuffisant"


def calculer(points, evaluations):
    """points : liste de tuples de rubriques.py ; evaluations : {code: 'C'|'PC'|'NC'|'NA'|None}."""
    obtenus = maximum = nb_eval = nb_nc_crit = 0
    nb = {k: 0 for k in EVALUATIONS}
    for code, _aspect, _zone, _critere, critique in points:
        ev = evaluations.get(code)
        if not ev:
            continue
        nb_eval += 1
        nb[ev] += 1
        if ev == "NC" and critique:
            nb_nc_crit += 1
        pts = EVALUATIONS[ev][1]
        if pts is not None:
            obtenus += pts * coef(critique)
            maximum += POINTS_MAX * coef(critique)
    score = round(100 * obtenus / maximum, 1) if maximum else None
    return {"obtenus": obtenus, "max": maximum, "score": score, "nb_evalues": nb_eval,
            "nb_total": len(points), "nb": nb, "nb_nc_critiques": nb_nc_crit,
            "resultat": resultat(score, nb_nc_crit)}


# --- Base de données -------------------------------------------------------

meta = MetaData()

audits = Table(
    "audits", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rubrique", String(50), nullable=False, index=True),
    Column("magasin", String(200), nullable=False),
    Column("auditeur", String(200), nullable=False),
    Column("personne_auditee", String(200)),
    Column("date_audit", String(10), nullable=False),   # AAAA-MM-JJ
    Column("points_obtenus", Integer, nullable=False),
    Column("points_max", Integer, nullable=False),
    Column("score", Float),                              # points obtenus / points max, en %
    Column("resultat", String(50)),
    Column("nb_points_total", Integer, nullable=False),
    Column("nb_evalues", Integer, nullable=False),
    Column("nb_c", Integer, nullable=False),
    Column("nb_pc", Integer, nullable=False),
    Column("nb_nc", Integer, nullable=False),
    Column("nb_na", Integer, nullable=False),
    Column("nb_nc_critiques", Integer, nullable=False),
    Column("commentaire", Text),
    Column("created_at", String(19), nullable=False),
)

audit_reponses = Table(
    "audit_reponses", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("audit_id", Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("point_code", String(20), nullable=False),
    Column("aspect", String(200), nullable=False),
    Column("zone", String(200), nullable=False),
    Column("critere", Text, nullable=False),
    Column("point_critique", Integer, nullable=False),
    Column("coef", Integer, nullable=False),
    Column("evaluation", String(2)),                     # C / PC / NC / NA, vide = non évalué
    Column("points", Integer),
    Column("points_max", Integer),
    Column("observations", Text),
    Column("action_corrective", Text),
    Column("responsable", String(200)),
    Column("delai", String(10)),
)


def url_base(url=None):
    url = url or os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'audits.db')}"
    # Les URL fournies par Neon / Supabase commencent par postgres:// ou postgresql://
    for prefixe in ("postgres://", "postgresql://"):
        if url.startswith(prefixe):
            return "postgresql+psycopg://" + url[len(prefixe):]
    return url


def moteur(url=None):
    engine = create_engine(url_base(url), pool_pre_ping=True)
    with engine.begin() as conn:
        cols = [c["name"] for c in inspect(conn).get_columns("audits")] if inspect(conn).has_table("audits") else []
        if cols and "resultat" not in cols:
            # Base de la toute première version : conservée sous un autre nom.
            conn.execute(text("ALTER TABLE audit_reponses RENAME TO audit_reponses_v1"))
            conn.execute(text("ALTER TABLE audits RENAME TO audits_v1"))
            conn.execute(text("DROP INDEX IF EXISTS idx_audits_rubrique"))
            conn.execute(text("DROP INDEX IF EXISTS idx_reponses_audit"))
    meta.create_all(engine)
    return engine


def valider(code, entete, evaluations, details):
    points = RUBRIQUES[code]["points"]
    erreurs = []
    if not (entete.get("magasin") or "").strip():
        erreurs.append("Le magasin est obligatoire.")
    if not (entete.get("auditeur") or "").strip():
        erreurs.append("L'auditeur est obligatoire.")
    if not entete.get("date_audit"):
        erreurs.append("La date d'audit est obligatoire.")
    for pcode, _a, _z, critere, _c in points:
        d = details.get(pcode, {})
        if evaluations.get(pcode) == "NC" and not ((d.get("observations") or "").strip()
                                                   and (d.get("action_corrective") or "").strip()):
            erreurs.append(f"NC sans observation ou action corrective : {critere}")
    if not any(evaluations.get(p[0]) for p in points):
        erreurs.append("Aucun critère n'a été évalué.")
    return erreurs


def enregistrer_fiche(engine, code, entete, evaluations, details):
    """entete : magasin, auditeur, personne_auditee, date_audit (AAAA-MM-JJ), commentaire.
    details : {code_point: {observations, action_corrective, responsable, delai}}.
    Retourne (id, erreurs)."""
    erreurs = valider(code, entete, evaluations, details)
    if erreurs:
        return None, erreurs
    points = RUBRIQUES[code]["points"]
    calc = calculer(points, evaluations)
    propre = lambda v: (v or "").strip() or None
    with engine.begin() as conn:
        audit_id = conn.execute(insert(audits).values(
            rubrique=code, magasin=entete["magasin"].strip(), auditeur=entete["auditeur"].strip(),
            personne_auditee=propre(entete.get("personne_auditee")), date_audit=str(entete["date_audit"]),
            points_obtenus=calc["obtenus"], points_max=calc["max"], score=calc["score"],
            resultat=calc["resultat"], nb_points_total=calc["nb_total"], nb_evalues=calc["nb_evalues"],
            nb_c=calc["nb"]["C"], nb_pc=calc["nb"]["PC"], nb_nc=calc["nb"]["NC"], nb_na=calc["nb"]["NA"],
            nb_nc_critiques=calc["nb_nc_critiques"], commentaire=propre(entete.get("commentaire")),
            created_at=datetime.now().isoformat(timespec="seconds"),
        )).inserted_primary_key[0]
        lignes = []
        for pcode, aspect, zone, critere, critique in points:
            ev = evaluations.get(pcode) or None
            pts = EVALUATIONS[ev][1] if ev else None
            d = details.get(pcode, {})
            lignes.append(dict(
                audit_id=audit_id, point_code=pcode, aspect=aspect, zone=zone, critere=critere,
                point_critique=int(critique), coef=coef(critique), evaluation=ev,
                points=None if pts is None else pts * coef(critique),
                points_max=None if pts is None else POINTS_MAX * coef(critique),
                observations=propre(d.get("observations")), action_corrective=propre(d.get("action_corrective")),
                responsable=propre(d.get("responsable")), delai=str(d["delai"]) if d.get("delai") else None))
        conn.execute(insert(audit_reponses), lignes)
    return audit_id, []


def stats_rubriques(engine):
    q = select(audits.c.rubrique, func.count().label("n"), func.max(audits.c.date_audit).label("dernier"),
               func.avg(audits.c.score).label("moy")).group_by(audits.c.rubrique)
    with engine.connect() as conn:
        return {r.rubrique: r for r in conn.execute(q)}


def liste_fiches(engine, rubrique=None):
    q = select(audits).order_by(audits.c.date_audit.desc(), audits.c.id.desc())
    if rubrique:
        q = q.where(audits.c.rubrique == rubrique)
    with engine.connect() as conn:
        return [r._mapping for r in conn.execute(q)]


def lire_fiche(engine, audit_id):
    with engine.connect() as conn:
        a = conn.execute(select(audits).where(audits.c.id == audit_id)).first()
        if not a:
            return None, []
        reps = conn.execute(select(audit_reponses).where(audit_reponses.c.audit_id == audit_id)
                            .order_by(audit_reponses.c.id)).all()
    return a._mapping, [r._mapping for r in reps]
