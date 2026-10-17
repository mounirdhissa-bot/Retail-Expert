"""Application d'audit retail (Streamlit) : saisie des fiches d'audit et historisation.

Lancement local :  streamlit run app.py
En ligne : renseigner DATABASE_URL dans les secrets Streamlit pour une base Postgres persistante.
"""

import hmac
import os
from datetime import date

import pandas as pd
import streamlit as st

import audit_core as core
import ui
from rubriques import (COEF_CRITIQUE, EVALUATIONS, RUBRIQUES, SEUIL_A_AMELIORER,
                       SEUIL_SATISFAISANT)

st.set_page_config(page_title="Audit Retail", page_icon=":material/fact_check:", layout="wide")
ui.css()


@st.cache_resource
def engine():
    return core.moteur(secret("DATABASE_URL"))


def secret(nom):
    try:
        return st.secrets.get(nom) or os.environ.get(nom)
    except Exception:  # pas de fichier secrets en local
        return os.environ.get(nom)


ss = st.session_state

# Accès protégé par mot de passe dès que APP_PASSWORD est défini (secrets Streamlit).
MOT_DE_PASSE = secret("APP_PASSWORD")
if MOT_DE_PASSE and not ss.get("connecte"):
    ui.bandeau("Audit Retail", "Accès réservé : saisissez le mot de passe.", "lock", ui.MARINE,
               fond=ui.FOND_MARQUE, logos=True)
    with st.form("connexion"):
        saisi = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter", type="primary"):
            if hmac.compare_digest(saisi, MOT_DE_PASSE):
                ss.connecte = True
                st.rerun()
            st.error("Mot de passe incorrect.")
    st.stop()
ss.setdefault("page", "Accueil")
ss.setdefault("rubrique", next(iter(RUBRIQUES)))
ss.setdefault("version_form", 0)
ss.setdefault("fiche_id", None)
ss.setdefault("message", None)

PAGES = ["Accueil", "Nouvelle fiche", "Historique"]
ICONES_PAGES = {"Accueil": ":material/home:", "Nouvelle fiche": ":material/edit_note:",
                "Historique": ":material/history:"}


def aller(page, **etat):
    ss.update(etat)
    ss.page = page
    ss.nav_cible = page if page in PAGES else "Historique"  # appliqué avant de recréer le menu


def score_txt(score):
    return "–" if score is None else f"{score:.0f} %"


def grouper(points):
    groupes = {}
    for n, p in enumerate(points, 1):
        groupes.setdefault(p[1], {}).setdefault(p[2], []).append((n, p))
    return groupes


# --- Barre latérale ---------------------------------------------------------

with st.sidebar:
    ui.marque()
    ui.logos_marques()
    if "nav_cible" in ss:
        ss.nav = ss.pop("nav_cible")
    ss.setdefault("nav", ss.page)
    st.radio("Navigation", PAGES, key="nav", label_visibility="collapsed",
             format_func=lambda p: f"{ICONES_PAGES[p]} {p}", on_change=lambda: ss.update(page=ss.nav))

    # Base active : permet de vérifier que l'application en ligne écrit bien dans Neon.
    info = core.info_base(engine())
    if info["type"] == "postgresql":
        st.success(f"Base : PostgreSQL ({info['hote']}) · {info['nb_fiches']} fiche(s)", icon="🗄️")
    elif os.path.isdir("/mount/src"):  # répertoire des applications Streamlit Community Cloud
        st.error("Base : SQLite temporaire. DATABASE_URL n'est pas défini dans les secrets : "
                 "les fiches seront perdues au prochain redémarrage.", icon="⚠️")
    else:
        st.info(f"Base : SQLite locale · {info['nb_fiches']} fiche(s)", icon="🗄️")


# --- Accueil ----------------------------------------------------------------

def page_accueil():
    ui.bandeau("Fiches d'audit", "Choisissez une rubrique pour renseigner une nouvelle fiche d'audit.",
               "fact_check", ui.MARINE, fond=ui.FOND_MARQUE, logos=True)
    fiches = core.liste_fiches(engine())
    scores = [f["score"] for f in fiches if f["score"] is not None]
    moyenne = sum(scores) / len(scores) if scores else None
    ui.kpis([
        ("description", "Fiches enregistrées", len(fiches), ui.MARINE),
        ("speed", "Score moyen", score_txt(moyenne), ui.couleur_score(moyenne), True),
        ("report", "NC sur points critiques", sum(f["nb_nc_critiques"] for f in fiches), ui.ROUGE),
        ("event", "Dernier audit", max((f["date_audit"] for f in fiches), default="–"), "#0EA5E9"),
    ])
    stats = core.stats_rubriques(engine())
    colonnes = st.columns(3, gap="medium")
    for i, (code, rub) in enumerate(RUBRIQUES.items()):
        with colonnes[i % 3].container(border=True, key=f"carte_{code}"):
            s = stats.get(code)
            puces = [f"{len(rub['points'])} critères"]
            puces += ([f"{s.n} fiche(s)", f"Moyenne {score_txt(s.moy)}", f"Dernier : {s.dernier}"]
                      if s else ["Aucune fiche"])
            ui.tete_rubrique(rub, puces)
            st.button("Remplir une fiche", key=f"go_{code}", icon=":material/add_circle:", on_click=aller,
                      args=("Nouvelle fiche",), kwargs={"rubrique": code}, width="stretch")


# --- Formulaire -------------------------------------------------------------

def page_formulaire():
    codes = list(RUBRIQUES)
    code = st.selectbox("Rubrique", codes, index=codes.index(ss.rubrique),
                        format_func=lambda c: RUBRIQUES[c]["titre"])
    ss.rubrique = code
    rub = RUBRIQUES[code]
    k = f"v{ss.version_form}_{code}_"  # change après chaque Submit pour vider le formulaire

    ui.bandeau(rub["titre"], rub["description"], rub["icone"], rub["couleur"])

    with st.container(border=True):
        st.markdown("**En-tête**")
        c1, c2, c3, c4 = st.columns(4)
        entete = {
            "magasin": c1.text_input("Magasin *", key=k + "magasin"),
            "auditeur": c2.text_input("Auditeur *", key=k + "auditeur"),
            "personne_auditee": c3.text_input("Personne auditée", key=k + "personne"),
            "date_audit": c4.date_input("Date de l'audit *", value=date.today(), key=k + "date", format="DD/MM/YYYY"),
        }
        st.caption(" · ".join(f"**{v}** {lib}" + (f" ({p} pt{'s' if p > 1 else ''})" if p is not None else " (exclu)")
                              for v, (lib, p) in EVALUATIONS.items())
                   + f". Point critique : coefficient {COEF_CRITIQUE}. Un critère laissé vide est non évalué. "
                     "Une NC demande une observation et une action corrective.")

    evaluations, details = {}, {}
    for aspect, zones in grouper(rub["points"]).items():
        ui.section(aspect, rub["couleur"], rub["icone"])
        for zone, pts in zones.items():
            ui.zone(zone)
            for n, (pcode, _a, _z, critere, critique) in pts:
                with st.container(border=True):
                    libelle = f"{n}. {critere}" + (f"  :red-badge[Point critique ×{COEF_CRITIQUE}]" if critique else "")
                    ev = st.radio(libelle, list(EVALUATIONS), index=None, horizontal=True, key=k + "ev_" + pcode,
                                  format_func=lambda v: f"{v} · {EVALUATIONS[v][0]}")
                    evaluations[pcode] = ev
                    with st.expander("Observations et action corrective" + (" (obligatoire)" if ev == "NC" else ""),
                                     expanded=ev == "NC"):
                        d1, d2, d3, d4 = st.columns([3, 3, 2, 2])
                        details[pcode] = {
                            "observations": d1.text_input("Observations", key=k + "obs_" + pcode),
                            "action_corrective": d2.text_input("Action corrective", key=k + "act_" + pcode),
                            "responsable": d3.text_input("Responsable", key=k + "resp_" + pcode),
                            "delai": d4.date_input("Délai", value=None, key=k + "delai_" + pcode, format="DD/MM/YYYY"),
                        }
    entete["commentaire"] = st.text_area("Commentaire général", key=k + "commentaire")

    # Score en direct, dans la barre latérale
    calc = core.calculer(rub["points"], evaluations)
    with st.sidebar:
        st.divider()
        st.markdown("**Fiche en cours**")
        st.metric("Score", score_txt(calc["score"]))
        st.markdown("Résultat : " + ui.badge(calc["resultat"] or "–", ui.couleur_resultat(calc["resultat"])),
                    unsafe_allow_html=True)
        st.caption(f"Points {calc['obtenus']} / {calc['max']} · évalués {calc['nb_evalues']} / {calc['nb_total']} · "
                   f"NC {calc['nb']['NC']} (dont {calc['nb_nc_critiques']} critique{'s' if calc['nb_nc_critiques'] > 1 else ''})")

    if st.button("Submit", type="primary", icon=":material/send:"):
        audit_id, erreurs = core.enregistrer_fiche(engine(), code, entete, evaluations, details)
        if erreurs:
            st.error("Fiche non enregistrée :\n\n" + "\n".join(f"- {x}" for x in erreurs))
        else:
            ss.version_form += 1
            ss.message = "La fiche a bien été enregistrée."
            aller("Fiche", fiche_id=audit_id)
            st.rerun()


# --- Fiche enregistrée ------------------------------------------------------

def page_fiche():
    a, reps = core.lire_fiche(engine(), ss.fiche_id)
    if not a:
        st.warning("Fiche introuvable.")
        return
    if ss.message:
        st.success(ss.message)
        ss.message = None
    rub = RUBRIQUES.get(a["rubrique"], {"titre": a["rubrique"], "icone": "fact_check", "couleur": ui.MARINE})
    titre = rub["titre"]
    personne = f" · personne auditée : {a['personne_auditee']}" if a["personne_auditee"] else ""
    ui.bandeau(f"{titre} · fiche n°{a['id']}",
               f"{a['magasin']} · auditeur : {a['auditeur']}{personne} · {a['date_audit']}", rub["icone"], rub["couleur"])
    ui.kpis([
        ("speed", "Score global", score_txt(a["score"]), ui.couleur_score(a["score"]), True),
        ("verified", "Résultat", a["resultat"] or "–", ui.couleur_resultat(a["resultat"]), True),
        ("scoreboard", "Points obtenus / max", f"{a['points_obtenus']} / {a['points_max']}", rub["couleur"]),
        ("checklist", "Évalués / total", f"{a['nb_evalues']} / {a['nb_points_total']}", rub["couleur"]),
        ("rule", "C · PC · NC · NA", f"{a['nb_c']} · {a['nb_pc']} · {a['nb_nc']} · {a['nb_na']}", "#64748B"),
        ("report", "NC critiques", a["nb_nc_critiques"], ui.ROUGE, a["nb_nc_critiques"] > 0),
    ])

    df = pd.DataFrame(reps)
    texte = ["observations", "action_corrective", "responsable", "delai"]
    df[texte] = df[texte].fillna("")
    ui.section("Score par aspect", rub["couleur"], "bar_chart")
    asp = (df.groupby("aspect", sort=False)
             .agg(points=("points", "sum"), max=("points_max", "sum"), nc=("evaluation", lambda s: (s == "NC").sum()))
             .reset_index())
    asp["score"] = (100 * asp["points"] / asp["max"].where(asp["max"] > 0)).round(0)
    st.dataframe(asp.rename(columns={"aspect": "Aspect", "points": "Points", "max": "Max", "nc": "NC", "score": "Score %"}),
                 hide_index=True, width="stretch",
                 column_config={"Score %": st.column_config.ProgressColumn("Score %", min_value=0, max_value=100, format="%d %%")})

    plan = df[df["evaluation"].isin(["NC", "PC"])]
    if len(plan):
        ui.section("Plan d'action", ui.ROUGE, "assignment_late")
        st.dataframe(plan[["critere", "evaluation", "observations", "action_corrective", "responsable", "delai"]]
                     .rename(columns={"critere": "Critère", "evaluation": "Éval.", "observations": "Observations",
                                      "action_corrective": "Action corrective", "responsable": "Responsable",
                                      "delai": "Délai"}), hide_index=True, width="stretch")

    ui.section("Détail des critères", "#64748B", "list_alt")
    det = df.assign(n=range(1, len(df) + 1), critique=df["point_critique"].astype(bool),
                    evaluation=df["evaluation"].fillna("non évalué"))
    st.dataframe(det[["n", "aspect", "zone", "critere", "critique", "evaluation", "points", "points_max",
                      "observations", "action_corrective", "responsable", "delai"]]
                 .rename(columns={"n": "N°", "aspect": "Aspect", "zone": "Zone", "critere": "Critère",
                                  "critique": "Critique", "evaluation": "Éval.", "points": "Points", "points_max": "Max",
                                  "observations": "Observations", "action_corrective": "Action corrective",
                                  "responsable": "Responsable", "delai": "Délai"}),
                 hide_index=True, width="stretch")
    if a["commentaire"]:
        st.subheader("Commentaire général")
        st.write(a["commentaire"])
    st.button(f"Nouvelle fiche {titre}", icon=":material/add_circle:", on_click=aller, args=("Nouvelle fiche",), kwargs={"rubrique": a["rubrique"]})


# --- Historique -------------------------------------------------------------

def page_historique():
    ui.bandeau("Historique des audits", "Toutes les fiches enregistrées, filtrables par rubrique.", "history", ui.MARINE,
               fond=ui.FOND_MARQUE)
    filtre = st.selectbox("Rubrique", [None] + list(RUBRIQUES),
                          format_func=lambda c: "Toutes" if c is None else RUBRIQUES[c]["titre"])
    fiches = core.liste_fiches(engine(), filtre)
    if not fiches:
        st.info("Aucune fiche enregistrée pour le moment.")
        return
    df = pd.DataFrame(fiches)
    df["rubrique"] = df["rubrique"].map(lambda c: RUBRIQUES.get(c, {}).get("titre", c))
    df["personne_auditee"] = df["personne_auditee"].fillna("")
    vue = df[["id", "date_audit", "rubrique", "magasin", "personne_auditee", "auditeur", "score", "resultat",
              "nb_nc", "nb_nc_critiques"]].rename(columns={
        "id": "Fiche", "date_audit": "Date", "rubrique": "Rubrique", "magasin": "Magasin",
        "personne_auditee": "Personne auditée", "auditeur": "Auditeur", "score": "Score %",
        "resultat": "Résultat", "nb_nc": "NC", "nb_nc_critiques": "NC critiques"})
    sel = st.dataframe(vue, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
                       column_config={"Score %": st.column_config.ProgressColumn("Score %", min_value=0, max_value=100,
                                                                                format="%d %%")})
    st.caption("Cliquez sur une ligne pour ouvrir la fiche.")
    if sel.selection.rows:
        aller("Fiche", fiche_id=int(vue.iloc[sel.selection.rows[0]]["Fiche"]))
        st.rerun()
    st.download_button("Télécharger l'historique (CSV)", vue.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       "historique_audits.csv", "text/csv", icon=":material/download:")


{"Accueil": page_accueil, "Nouvelle fiche": page_formulaire,
 "Historique": page_historique, "Fiche": page_fiche}[ss.page]()
