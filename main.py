import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium
import zipfile
import io
import requests

# Téléchargement des données  
@st.cache_data  
def load_data():
    # Chargement des fichiers Parquet locaux  
    orders_customers_df = pd.read_parquet("orders_customers_df.parquet")
    geolocation_df = pd.read_parquet("geolocation_df.parquet")
    order_items_df = pd.read_parquet("order_items_df.parquet")
    order_payments_df = pd.read_parquet("order_payments_df.parquet")
    order_reviews_df = pd.read_parquet("order_reviews_df.parquet")
    order_df = pd.read_parquet("order_df.parquet")
    products_df = pd.read_parquet("products_df.parquet")
    sellers_df = pd.read_parquet("sellers_df.parquet")
    
    return (orders_customers_df, geolocation_df, order_items_df, 
            order_payments_df, order_reviews_df, order_df, products_df, sellers_df)

# Charger les données  
orders_customers_df, geolocation_df, order_items_df, order_payments_df, order_reviews_df, order_df, products_df, sellers_df = load_data()

# Titre de l'application
st.title("Tableau de Bord : Satisfaction des Clients Olist")
st.write("Ce tableau de bord vise à analyser et améliorer la satisfaction client sur Olist.")

# Onglets pour organiser le contenu
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Répartition des notes", "Impact des retards", "Performance des vendeurs", "Moyens de paiement", "Carte géographique", "Recommandations"])

### 1. Répartition des notes
with tab1:
    st.header("Répartition des notes clients")
    fig, ax = plt.subplots()
    sns.countplot(data=order_reviews_df, x='review_score', palette='viridis', ax=ax)
    ax.set_title("Répartition des notes clients")
    ax.set_xlabel("Note")
    ax.set_ylabel("Nombre de commandes")
    st.pyplot(fig)
    st.markdown("**Commentaire** : En analysant la distribution des notes clients d'Olist, nous constatons une majorité de notes excellentes (5/5) mais également un volume préoccupant de notes très basses (1/5). Pour améliorer la satisfaction client, une priorité devrait être d'analyser les causes d'insatisfaction de ce segment critique d'utilisateurs mécontents et d'implémenter des actions correctives ciblées.")

### 2. Impact des retards
with tab2:
    st.header("Impact des retards sur les notes")
    order_df['order_delivered_customer_date'] = pd.to_datetime(order_df['order_delivered_customer_date'])
    order_df['order_estimated_delivery_date'] = pd.to_datetime(order_df['order_estimated_delivery_date'])
    order_df['delayed'] = order_df['order_delivered_customer_date'] > order_df['order_estimated_delivery_date']
    merged_df = order_df.merge(order_reviews_df[['order_id', 'review_score']], on='order_id')
    fig, ax = plt.subplots()
    sns.boxplot(data=merged_df, x='delayed', y='review_score', palette='Set2', ax=ax)
    ax.set_title("Impact des retards sur les notes")
    ax.set_xlabel("En retard ?")
    ax.set_ylabel("Note moyenne")
    st.pyplot(fig)
    st.markdown("**Commentaire** : Ce graphique montre clairement l'impact des retards sur la satisfaction client chez Olist. À gauche (False), nous voyons les notes des commandes livrées à temps : la majorité se situe entre 4 et 5 étoiles, avec une médiane autour de 4.5. C'est excellent! À droite (True), pour les commandes en retard, la situation est préoccupante : les notes sont beaucoup plus dispersées, avec une médiane autour de 2 étoiles seulement. Les clients peuvent noter entre 1 et 5, mais la plupart des évaluations sont nettement plus basses. Cette analyse complète notre observation précédente sur les notes négatives : les retards de livraison semblent être une cause majeure d'insatisfaction. Pour améliorer la satisfaction globale, il serait prioritaire d'optimiser les délais de livraison et la gestion des attentes clients concernant ces délais.")

### 3. Performance des vendeurs avec tableau croisé
with tab3:
    st.header("Performance des vendeurs")
    
    # Calcul des taux de retard
    orders_sellers_df = order_items_df[['order_id', 'seller_id']].merge(order_df[['order_id', 'delayed']], on='order_id')
    delays_by_seller = orders_sellers_df.groupby('seller_id')['delayed'].mean().reset_index()

    # Ajout du filtre pour taux de retard
    st.subheader("Filtrer les vendeurs par taux de retard")
    threshold = st.slider("Taux de retard maximum (%)", 0, 100, 10) / 100  # Convertir en proportion
    filtered_sellers = delays_by_seller[delays_by_seller['delayed'] <= threshold]
    st.dataframe(filtered_sellers)

    # Graphique des top 10 vendeurs les plus en retard
    st.subheader("Top 10 des vendeurs les plus en retard")
    top_10_late_sellers = filtered_sellers.sort_values(by='delayed', ascending=False).head(10)
    fig, ax = plt.subplots()
    sns.barplot(data=top_10_late_sellers, x='delayed', y='seller_id', palette='Reds_r', ax=ax)
    ax.set_title("Top 10 des vendeurs les plus en retard")
    ax.set_xlabel("Taux de commandes en retard")
    ax.set_ylabel("Seller ID")
    st.pyplot(fig)
    st.markdown("**Commentaire** : Ce graphique permet de cibler les vendeurs les moins performants pour des actions correctives spécifiques. Possibilité de se rapprocher d'eux pour savoir les éléments bloquants justifiants ces retards afin d'y remedier. Une autre possibilité est aussi de les sensibiliser sur le respect des délais et des impacts sur l'image de marque de l'entreprise ainsi que sur le business de manière globale.")

    # Analyse supplémentaire : Nombre de vendeurs avec > 5% de retards
    st.subheader("Statistiques globales sur les retards des vendeurs")
    nb_vendeurs_en_retard = (delays_by_seller['delayed'] > 0.05).sum()
    nb_total_vendeurs = delays_by_seller['seller_id'].nunique()
    pourcentage = round((nb_vendeurs_en_retard / nb_total_vendeurs) * 100, 2)

    st.markdown(f"**Nombre de vendeurs avec > 5% de retards** : {nb_vendeurs_en_retard}")
    st.markdown(f"**Nombre total de vendeurs** : {nb_total_vendeurs}")
    st.markdown(f"**Pourcentage de vendeurs en retard > 5%** : {pourcentage}%")

    # Regroupement des vendeurs en 2 catégories pour visualisation
    delays_by_seller['retardé_>_0.05'] = delays_by_seller['delayed'] > 0.05
    group_counts = delays_by_seller['retardé_>_0.05'].value_counts()

    # Visualisation des catégories
    st.subheader("Répartition des vendeurs selon leur taux de retard")
    fig, ax = plt.subplots(figsize=(6, 4))
    group_counts.plot(kind='bar', color=['green', 'red'], ax=ax)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['≤ 5% retards', '> 5% retards'], rotation=0)
    ax.set_ylabel("Nombre de vendeurs")
    ax.set_title("Répartition des vendeurs selon leur taux de commandes en retard")
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    st.pyplot(fig)
    st.markdown("**Commentaire** : Cette visualisation montre qu'une majorité importante des vendeurs respecte le taux stricte de retards <= 5%. Toutefois une proportion significative de vendeurs ont un taux de retard supérieur à ce seuil, nécessitant des actions d'amélioration comme mentionné précédemment. La baisse du nombre de vendeurs au dessus de ce seuil devrait entrainer un changement positif sur la satisfaction cleints.")

### 4. Moyens de paiement
with tab4:
    st.header("Moyens de paiement problématiques")
    merged = order_payments_df.merge(order_reviews_df, on="order_id")
    score_by_payment = merged.groupby("payment_type")["review_score"].mean().sort_values()
    fig, ax = plt.subplots()
    score_by_payment.plot(kind="bar", color="orange", title="Note moyenne par moyen de paiement", ax=ax)
    ax.set_ylabel("Note moyenne")
    st.pyplot(fig)
    st.markdown("**Commentaire** : Le graphique montre une différence importante dans la satisfaction client selon le moyen de paiement utilisé. La plupart des méthodes (voucher, boleto, credit_card et debit_card) obtiennent des notes moyennes satisfaisantes autour de 4/5. En revanche, la catégorie 'not defined' présente une note moyenne très basse d'environ 1.7/5. Cette anomalie suggère un problème significatif avec les transactions dont le mode de paiement n'est pas correctement enregistré, ce qui pourrait être une piste d'amélioration prioritaire pour augmenter la satisfaction client globale. Pourquoi est-ce qu'il existe un mode de paiement non identifié ?")

### 5. Carte géographique

with tab5:

    st.header("Carte des retards de livraison")

    # Calcul des retards  
    order_df['order_delivered_customer_date'] = pd.to_datetime(order_df['order_delivered_customer_date'])
    order_df['order_estimated_delivery_date'] = pd.to_datetime(order_df['order_estimated_delivery_date'])
    order_df["delay"] = (order_df["order_delivered_customer_date"] - 
                         order_df["order_estimated_delivery_date"]).dt.days

    # Fusion correcte des datasets pour inclure les localisations  
    filtered_geo = orders_customers_df.merge(order_df, on="customer_id")\
                                      .merge(geolocation_df, 
                                             left_on="customer_zip_code_prefix", 
                                             right_on="geolocation_zip_code_prefix")

    # Filtrer les commandes avec des retards significatifs (> 5 jours)  
    filtered_geo = filtered_geo[filtered_geo["delay"] > 5]

    # Création de la carte Folium sans marqueur fixe  
    # On utilise le premier point de filtered_geo pour centrer la carte, s'il y en a  
    if not filtered_geo.empty:
        initial_location = [filtered_geo["geolocation_lat"].mean(), filtered_geo["geolocation_lng"].mean()]
    else:
        initial_location = [0, 0]  # Coordonnées par défaut si filtered_geo est vide

    map_filtered = folium.Map(location=initial_location, zoom_start=5)

    # Ajouter les marqueurs des données  
    marker_cluster = FastMarkerCluster(data=list(zip(filtered_geo["geolocation_lat"], filtered_geo["geolocation_lng"]))).add_to(map_filtered)

    # Afficher la carte  
    st_folium(map_filtered, width=725)

    st.markdown("**Commentaire** : Cette carte optimisée met en évidence les zones où les retards de livraison sont les plus fréquents.")


### 6. Recommandations
with tab6:
    st.header("Recommandations")
    st.write("""

Notre analyse des données Olist révèle plusieurs axes d'amélioration prioritaires :

1. **Réduire les retards de livraison** : Impact majeur démontré (baisse de 4.5 à 2/5 de satisfaction)

2. **Résoudre l'anomalie des paiements "not defined"** : Note moyenne catastrophique de 1.7/5

3. **Optimiser la logistique régionale** : Concentrer les efforts sur les zones moins bien desservies (Nord/Ouest)

4. **Programme de récupération clients** : Analyse systématique des notes <= 2/5 pour identifier les problèmes récurrents

5. **Formation des vendeurs** : Mise en place d'un programme d'excellence axé sur la ponctualité et la communication client
""")