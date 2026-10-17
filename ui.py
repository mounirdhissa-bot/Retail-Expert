"""Habillage graphique : thème, cartes et bandeaux colorés par rubrique."""

import base64
import html
import os

import streamlit as st

from rubriques import RUBRIQUES, SEUIL_A_AMELIORER, SEUIL_SATISFAISANT

e = lambda s: html.escape(str(s if s is not None else ""))

VERT, ORANGE, ROUGE, GRIS = "#16A34A", "#D97706", "#DC2626", "#64748B"
MARINE, CORAIL = "#152B52", "#E94E1B"  # couleurs des logos Fishop et La Table du Frais

DOSSIER_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGOS = [("logo_fishop.png", "Fishop Délices des Mers"), ("logo_table_du_frais.png", "La Table du Frais by Fishop")]


def image_base64(nom):
    with open(os.path.join(DOSSIER_ASSETS, nom), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def teinte(hex_couleur, alpha):
    """Couleur hexadécimale -> rgba transparente (fonds de pastilles et de bandeaux)."""
    r, g, b = (int(hex_couleur[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def icone(nom, taille=22, couleur="currentColor"):
    return f'<span class="mi" style="font-size:{taille}px;color:{couleur}">{nom}</span>'


def couleur_score(score):
    if score is None:
        return GRIS
    return VERT if score >= SEUIL_SATISFAISANT else ORANGE if score >= SEUIL_A_AMELIORER else ROUGE


def couleur_resultat(res):
    if not res:
        return GRIS
    return VERT if res == "Satisfaisant" else ORANGE if res == "À améliorer" else ROUGE


def css():
    regles = []
    for code, r in RUBRIQUES.items():
        c = r["couleur"]
        regles.append(f"""
.st-key-carte_{code} {{ border-top: 5px solid {c} !important; }}
.st-key-go_{code} button {{ background:{c}; border-color:{c}; color:#fff; }}
.st-key-go_{code} button:hover {{ background:{c}; filter:brightness(1.1); color:#fff; border-color:{c}; }}""")
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,1,0');
html, body, .stApp, .stMarkdown, button, input, textarea, select {{ font-family:'Inter', sans-serif; }}
.mi {{ font-family:'Material Symbols Rounded'; font-weight:normal; font-style:normal; line-height:1;
       display:inline-block; vertical-align:middle; -webkit-font-smoothing:antialiased; }}
.stApp {{ background:#F4F6FB; }}
header[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:2rem; max-width:1250px; }}
h1, h2, h3 {{ letter-spacing:-.01em; }}

/* Barre latérale sombre */
section[data-testid="stSidebar"] {{ background:linear-gradient(180deg,{MARINE} 0%,#0B1730 100%); }}
section[data-testid="stSidebar"] * {{ color:#E2E8F0; }}
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{ color:#fff; }}
section[data-testid="stSidebar"] hr {{ border-color:#334155; }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{ padding:8px 10px; border-radius:10px; margin-bottom:2px; width:100%; }}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:rgba(255,255,255,.06); }}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:rgba(233,78,27,.28); }}
.marque {{ display:flex; align-items:center; gap:10px; margin:0 0 18px; }}
.marque .logo {{ width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;
                 background:linear-gradient(135deg,{CORAIL},#F59E0B); }}
.marque b {{ font-size:19px; color:#fff; }} .marque small {{ display:block; color:#94A3B8; font-size:12px; }}

/* Conteneurs bordés = cartes blanches */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{ background:#fff; }}
div[class*="st-key-carte_"] {{ background:#fff; border-radius:16px !important; box-shadow:0 1px 3px rgba(15,23,42,.06);
                               transition:transform .15s, box-shadow .15s; }}
div[class*="st-key-carte_"]:hover {{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(15,23,42,.10); }}
div[class*="st-key-go_"] button {{ border-radius:10px; font-weight:600; }}

/* Bandeau d'en-tête */
.bandeau {{ border-radius:18px; padding:26px 30px; color:#fff; margin-bottom:22px; display:flex; align-items:center; gap:18px;
            box-shadow:0 10px 30px rgba(15,23,42,.15); }}
.bandeau .pastille {{ width:62px; height:62px; border-radius:16px; background:rgba(255,255,255,.18);
                      display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.bandeau h1 {{ color:#fff; margin:0; padding:0; font-size:28px; font-weight:800; }}
.bandeau p {{ margin:4px 0 0; opacity:.9; }}
.bandeau .logos {{ margin-left:auto; display:flex; gap:14px; }}
.bandeau .logos img {{ width:92px; height:92px; border-radius:50%; background:#fff; padding:3px;
                       box-shadow:0 6px 18px rgba(0,0,0,.25); }}
.etat-base {{ background:#4ADE80; border-radius:12px; padding:12px 14px; display:flex; gap:10px; align-items:flex-start;
              font-size:14px; font-weight:600; word-break:break-word; margin-top:8px; }}
section[data-testid="stSidebar"] .etat-base, section[data-testid="stSidebar"] .etat-base * {{ color:#052E16; }}
.marques {{ display:flex; justify-content:center; gap:12px; margin:6px 0 16px; }}
.marques img {{ width:64px; height:64px; border-radius:50%; background:#fff; padding:2px; }}
@media (max-width:700px) {{ .bandeau {{ flex-wrap:wrap; }} .bandeau .logos {{ margin-left:0; }}
                            .bandeau .logos img {{ width:64px; height:64px; }} }}

/* Cartes rubriques (contenu HTML) */
.rub-tete {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; }}
.rub-tete .pastille {{ width:48px; height:48px; border-radius:14px; display:flex; align-items:center; justify-content:center; }}
.rub-tete h3 {{ margin:0; padding:0; font-size:18px; font-weight:700; color:#0F172A; }}
.rub-desc {{ color:#475569; font-size:14px; min-height:42px; margin-bottom:12px; }}
.puces {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:6px; }}
.puce {{ font-size:12px; font-weight:600; border-radius:999px; padding:3px 10px; background:#F1F5F9; color:#334155; }}

/* Indicateurs */
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin-bottom:22px; }}
.kpi {{ background:#fff; border-radius:16px; padding:16px 18px; box-shadow:0 1px 3px rgba(15,23,42,.06);
        display:flex; gap:14px; align-items:center; }}
.kpi .pastille {{ width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.kpi small {{ color:#64748B; font-size:12.5px; display:block; }} .kpi b {{ font-size:22px; color:#0F172A; }}

/* Titres de section dans le formulaire */
.section {{ display:flex; align-items:center; gap:10px; margin:26px 0 10px; padding:10px 14px; border-radius:12px; }}
.section b {{ font-size:17px; color:#0F172A; }}
.zone {{ font-size:12.5px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#64748B; margin:14px 0 6px 4px; }}
.badge {{ display:inline-block; font-weight:700; border-radius:999px; padding:6px 14px; font-size:15px; }}
.stButton button[kind="primary"] {{ border-radius:10px; font-weight:700; padding:.6rem 2.2rem; }}
{''.join(regles)}
</style>""", unsafe_allow_html=True)


def marque():
    st.markdown(f"""<div class="marque"><div class="logo">{icone('fact_check', 24, '#fff')}</div>
<div><b>Retail Expert</b><small>Suivi de la performance</small></div></div>""", unsafe_allow_html=True)


def bandeau(titre, sous_titre, nom_icone, couleur, fond=None, logos=False):
    fond = fond or f"linear-gradient(120deg, {couleur} 0%, {teinte(couleur, .78)} 60%, #0F172A 160%)"
    images = ""
    if logos:
        images = '<div class="logos">' + "".join(
            f'<img src="{image_base64(f)}" alt="{e(nom)}" title="{e(nom)}">' for f, nom in LOGOS) + "</div>"
    st.markdown(f"""<div class="bandeau" style="background:{fond}"><div class="pastille">{icone(nom_icone, 36, '#fff')}</div>
<div><h1>{e(titre)}</h1><p>{e(sous_titre)}</p></div>{images}</div>""", unsafe_allow_html=True)


FOND_MARQUE = f"linear-gradient(115deg, {MARINE} 0%, {MARINE} 45%, {CORAIL} 120%)"


def logos_marques():
    st.markdown('<div class="marques">' + "".join(
        f'<img src="{image_base64(f)}" alt="{e(nom)}" title="{e(nom)}">' for f, nom in LOGOS) + "</div>",
        unsafe_allow_html=True)


def kpis(elements):
    """elements : liste de (icône, libellé, valeur, couleur) ; la valeur prend la couleur si colorer=True
    est ajouté en 5e position."""
    cartes = []
    for i, libelle, valeur, c, *colorer in elements:
        couleur_valeur = c if colorer and colorer[0] else "#0F172A"
        taille = "font-size:16px" if len(str(valeur)) > 14 else ""  # textes longs (résultat)
        cartes.append(
            f'<div class="kpi"><div class="pastille" style="background:{teinte(c, .12)}">{icone(i, 24, c)}</div>'
            f'<div><small>{e(libelle)}</small><b style="color:{couleur_valeur};{taille}">{e(valeur)}</b></div></div>')
    cartes = "".join(cartes)
    st.markdown(f'<div class="kpis">{cartes}</div>', unsafe_allow_html=True)


def tete_rubrique(rub, puces):
    c = rub["couleur"]
    st.markdown(f"""<div class="rub-tete"><div class="pastille" style="background:{teinte(c, .12)}">{icone(rub['icone'], 28, c)}</div>
<h3>{e(rub['titre'])}</h3></div><div class="rub-desc">{e(rub['description'])}</div>
<div class="puces">{''.join(f'<span class="puce">{p}</span>' for p in puces)}</div>""", unsafe_allow_html=True)


def section(titre, couleur, nom_icone="label"):
    st.markdown(f"""<div class="section" style="background:{teinte(couleur, .10)};border-left:5px solid {couleur}">
{icone(nom_icone, 22, couleur)}<b>{e(titre)}</b></div>""", unsafe_allow_html=True)


def zone(titre):
    st.markdown(f'<div class="zone">{e(titre)}</div>', unsafe_allow_html=True)


def badge(texte, couleur):
    return f'<span class="badge" style="background:{teinte(couleur, .12)};color:{couleur}">{e(texte)}</span>'


def etat_base(texte):
    """Encadré vert clair de la barre latérale : l'application est branchée sur la base PostgreSQL."""
    st.markdown(f'<div class="etat-base">{icone("database", 20)}<span>{e(texte)}</span></div>', unsafe_allow_html=True)
