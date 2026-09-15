# Gestion d’événements

Application web Django permettant aux organisateurs de créer et de gérer des événements, et aux participants de consulter les événements à venir et de s’y inscrire. Elle comprend une gestion des comptes avec activation par e-mail, des profils personnalisables et un tableau de bord organisateur.

L’interface utilise principalement le français. Les prix sont affichés en euros et le fuseau horaire configuré est UTC.

> Ce README décrit le code présent dans le dépôt. Le paiement est simulé et certains parcours comportent des limites détaillées dans la section [État actuel et limites connues](#état-actuel-et-limites-connues).

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Structure du projet](#structure-du-projet)
- [Installation locale](#installation-locale)
- [Prise en main](#prise-en-main)
- [Routes principales](#routes-principales)
- [Modèle de données](#modèle-de-données)
- [Vérifications et tests](#vérifications-et-tests)
- [État actuel et limites connues](#état-actuel-et-limites-connues)

## Fonctionnalités

### Comptes et profils

- Inscription avec nom d’utilisateur, prénom, nom, e-mail et confirmation du mot de passe.
- Nom d’utilisateur alphanumérique de 5 à 10 caractères ; contrôle des doublons de nom d’utilisateur et d’e-mail à l’inscription.
- Création d’un compte participant inactif, puis activation par un lien envoyé par e-mail.
- Connexion par nom d’utilisateur et mot de passe, déconnexion et parcours de réinitialisation du mot de passe.
- Modification du profil : prénom, nom, e-mail, biographie, photo, téléphone, adresse et date de naissance.
- Choix du rôle **Participant** ou **Organisateur** depuis son propre profil.
- Administration Django des utilisateurs et des profils ; une route distincte permet aux superutilisateurs de modifier le rôle d’un autre utilisateur.

### Événements et inscriptions

- Création d’événements par les organisateurs : titre, description, image facultative, lieu, dates, capacité, catégorie, type gratuit ou payant et prix.
- Modification et suppression d’un événement par son propriétaire, avec confirmation de suppression.
- Liste des événements à venir, triée par date de début croissante et paginée à **9 événements par page**.
- Filtres visibles par catégorie, lieu et date. La vue accepte aussi les paramètres d’URL `search` et `type` (`FREE` ou `PAID`).
- Fiche détaillée avec places restantes et état de l’inscription.
- Inscription avec contrôle des doublons et des places restantes, puis tentative d’envoi d’un e-mail de confirmation.
- Sélection d’une visibilité publique ou privée et génération d’un lien d’invitation UUID, avec les limites de contrôle d’accès décrites plus bas.

### Tableau de bord organisateur

- Liste des événements de l’organisateur et accès aux actions de gestion.
- Nombre total d’événements et d’inscriptions.
- Nombre de billets d’événements payants marqués comme payés et revenu calculé correspondant.
- Places restantes, inscriptions et revenus par événement.
- Statuts **À venir**, **En cours** et **Terminé**.

## Technologies

| Élément | Utilisation dans le dépôt |
| --- | --- |
| Python / Django | Application côté serveur ; configuration et migrations générées avec Django **5.1.6** |
| SQLite | Base locale `db.sqlite3` |
| Templates Django | Rendu des pages HTML côté serveur |
| Bootstrap 5.3.0 | Mise en page et composants d’interface, chargés par CDN |
| Font Awesome 6.0.0 | Icônes, chargées par CDN |
| Flatpickr | Sélection des dates à la création d’un événement, chargée par CDN |
| Pillow | Prise en charge des champs d’image Django |
| six | Utilisé par le générateur de jetons d’activation |
| SMTP | Envoi des e-mails de compte et d’inscription |

Le dépôt ne contient pas de fichier `requirements.txt`, de `pyproject.toml` ni de chaîne de compilation JavaScript. Les dépendances Python ci-dessus sont identifiées à partir du code ; les versions de Pillow et de six ne sont pas fixées dans le dépôt.

## Structure du projet

```text
gestion-evenements/
├── manage.py                     # Commandes Django
├── config/
│   ├── settings.py               # Configuration générale, SQLite et médias
│   ├── info.py                   # Paramètres SMTP importés par settings.py
│   ├── urls.py                   # Routage principal
│   ├── asgi.py                   # Point d’entrée ASGI
│   └── wsgi.py                   # Point d’entrée WSGI
├── authentification/
│   ├── models.py                 # Utilisateur personnalisé et profil
│   ├── views.py                  # Comptes, activation et profils
│   ├── tokens.py                 # Jetons d’activation
│   ├── urls.py                   # Routes des comptes
│   ├── admin.py                  # Administration des utilisateurs et profils
│   └── migrations/
├── events/
│   ├── models.py                 # Catégories, événements et inscriptions
│   ├── views.py                  # Gestion des événements et tableau de bord
│   ├── urls.py                   # Routes sous /events/
│   ├── admin.py                  # Administration des données événementielles
│   ├── migrations/
│   ├── templates/events/         # Pages de gestion et de consultation
│   └── tests/
│       ├── test_models.py
│       └── test_views.py
├── templates/
│   ├── base.html                 # Base des pages de réinitialisation
│   ├── authentification/         # Accueil, comptes, profil et base principale
│   └── emailConfimation.html     # Message d’activation du compte
├── media/
│   ├── event_images/             # Images des événements
│   └── profile_pics/             # Photos de profil
├── db.sqlite3                    # Base incluse dans le dépôt
├── gitignore                     # Fichier présent sans point initial
└── README.md
```

## Installation locale

### 1. Préparer l’environnement Python

Depuis le dossier du projet, avec Python 3.12, `pip` et le module `venv` disponibles :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "Django==5.1.6" Pillow six
```

Sous Windows PowerShell, créer et activer l’environnement avec :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "Django==5.1.6" Pillow six
```

La version Django indiquée reproduit celle mentionnée dans les sources du projet ; cette procédure concerne une installation locale. Une connexion Internet est nécessaire pour télécharger les dépendances et charger les ressources d’interface externes.

### 2. Configurer les e-mails

Le fichier [config/info.py](config/info.py) fournit les paramètres SMTP. Adapter ses valeurs au compte d’envoi utilisé :

```python
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'votre-adresse@gmail.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-application'
EMAIL_PORT = 587
```

Les valeurs ci-dessus sont des exemples. Le projet importe directement ce fichier et ne charge pas de fichier `.env`.

L’inscription d’un compte envoie un message de bienvenue puis un message d’activation. Un échec SMTP peut interrompre ce parcours après la création du compte. L’e-mail de confirmation d’inscription à un événement utilise actuellement l’expéditeur `noreply@example.com` dans [events/views.py](events/views.py).

### 3. Préparer la base et l’administration

Le dépôt contient déjà une base SQLite et des images. Sauvegarder `db.sqlite3` et `media/` avant de travailler sur des données à conserver.

Depuis la racine du projet, avec l’environnement virtuel activé :

```bash
python manage.py migrate
python manage.py createsuperuser
```

Les migrations initiales des deux applications sont fournies. SQLite ne nécessite pas de serveur de base de données séparé.

### 4. Démarrer l’application

```bash
python manage.py runserver
```

- Application : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Administration : [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

Le dossier `static/` déclaré dans les paramètres est absent du dépôt : Django peut signaler l’avertissement `staticfiles.W004`. Les images téléversées dans `media/` sont servies par Django lorsque `DEBUG=True`.

## Prise en main

1. **Préparer les catégories** : se connecter à `/admin/` avec le superutilisateur et ajouter au moins une catégorie dans l’application Events si aucune n’existe. Une catégorie est obligatoire pour créer un événement.
2. **Créer un compte** : ouvrir `/signup`, renseigner les informations et activer le compte à partir du message reçu. Le lien d’activation comporte actuellement un préfixe mal formé ; consulter les limites ci-dessous.
3. **Se connecter** : ouvrir `/signin` et utiliser le nom d’utilisateur choisi à l’inscription.
4. **Devenir organisateur** : ouvrir `/profile/`, sélectionner le rôle Organisateur et enregistrer. Le rôle applicatif est distinct du statut de superutilisateur.
5. **Créer un événement** : ouvrir `/events/create/`, renseigner les champs obligatoires et sélectionner une catégorie. Pour un événement payant, saisir le prix du billet.
6. **Participer** : avec un compte connecté, ouvrir `/events/list/`, consulter une fiche puis s’inscrire. Le bouton « Acheter un billet » enregistre une inscription avec paiement simulé.
7. **Suivre les événements** : en tant qu’organisateur, consulter `/events/dashboard/`.

Exemple de recherche par URL, une fois connecté :

```text
/events/list/?search=concert&type=FREE&location=Conakry
```

## Routes principales

Les chemins ci-dessous sont relatifs à l’adresse de l’application. Les routes `signup`, `signin` et `signout` n’ont pas de barre oblique finale.

| Chemin | Usage |
| --- | --- |
| `/` | Accueil |
| `/signup` | Création d’un compte |
| `/signin` | Connexion |
| `/signout` | Déconnexion |
| `/activate/<uidb64>/<token>` | Activation d’un compte |
| `/password_reset/` | Demande de réinitialisation du mot de passe |
| `/password_reset/done/` | Confirmation de la demande |
| `/reset/<uidb64>/<token>/` | Définition d’un nouveau mot de passe |
| `/reset/done/` | Confirmation de la réinitialisation |
| `/profile/` | Consultation et modification du profil connecté |
| `/change-role/` | Modification du rôle d’un utilisateur par un superutilisateur, via POST |
| `/events/list/` | Liste et filtrage des événements à venir |
| `/events/<event_id>/` | Détail d’un événement |
| `/events/<event_id>/invite/<invitation_link>/` | Détail via un lien d’invitation |
| `/events/<event_id>/register/` | Inscription à un événement |
| `/events/create/` | Création par un organisateur |
| `/events/<event_id>/edit/` | Modification par le propriétaire |
| `/events/<event_id>/delete/` | Confirmation, puis suppression via POST par le propriétaire |
| `/events/dashboard/` | Tableau de bord organisateur |
| `/admin/` | Administration Django |

Toutes les vues de l’application `events` nécessitent une connexion, y compris la liste et les liens d’invitation.

## Modèle de données

| Modèle | Contenu et relations |
| --- | --- |
| `User` | Hérite de `AbstractUser` et ajoute le rôle Participant ou Organisateur |
| `Profile` | Profil lié à un seul utilisateur : coordonnées, biographie, photo et date de naissance |
| `Category` | Catégorie pouvant regrouper plusieurs événements |
| `Event` | Événement lié à un organisateur et à une catégorie, avec dates, capacité, tarif, visibilité et UUID d’invitation |
| `EventRegistration` | Inscription reliant un utilisateur à un événement, avec date d’inscription et état du paiement |

Un couple événement–participant est unique en base. Le nombre de places restantes correspond à la capacité totale (`available_seats`) moins le nombre d’inscriptions. Le revenu d’un événement payant correspond au prix du billet multiplié par le nombre d’inscriptions marquées comme payées.

Les relations utilisent `on_delete=models.CASCADE` : supprimer un événement supprime ses inscriptions ; supprimer sa catégorie ou son organisateur supprime aussi les événements associés.

## Vérifications et tests

Avec les dépendances installées et l’environnement virtuel activé :

```bash
python manage.py check
python manage.py test events.tests.test_models events.tests.test_views
```

Les modules sont ciblés explicitement car le dépôt contient à la fois `events/tests.py` et le dossier `events/tests/`.

Les **17 méthodes de test** présentes couvrent notamment les modèles, les places restantes, les dates invalides, le calcul des revenus, l’unicité des inscriptions et les principales vues de gestion. Le fichier `authentification/tests.py` ne contient pas encore de tests métier.

Les tests Django utilisent une base de test séparée et un backend d’e-mails en mémoire. Leur présence ne constitue pas une validation de tous les parcours, notamment des contrôles d’accès aux événements privés et de l’activation par e-mail.

## État actuel et limites connues

Ces points décrivent l’implémentation actuelle et permettent de comprendre les comportements rencontrés à l’utilisation.

- **Paiement simulé** : la vue d’inscription attribue directement `payment_status=True`, pour les événements gratuits comme payants. Aucun prestataire de paiement n’est intégré ; les revenus du tableau de bord sont calculés à partir de cet état.
- **Visibilité privée incohérente** : les formulaires et le filtrage utilisent `is_private`, tandis que l’accès à la fiche vérifie `is_public`. Ces deux champs ne sont pas synchronisés. Les organisateurs voient aussi tous les événements à venir dans la liste, et la vue d’inscription ne vérifie pas l’invitation. Le choix « Privé » ne garantit donc pas un accès limité aux invités.
- **Activation par e-mail** : le modèle `templates/emailConfimation.html` construit le lien avec `https//`, sans deux-points. Pour un essai local, reprendre le chemin `/activate/…` reçu et l’ouvrir avec le préfixe `http://127.0.0.1:8000`.
- **Connexion et redirections** : un nom d’utilisateur inexistant peut provoquer une exception dans la vue de connexion. `LOGIN_URL` n’est pas défini, alors que la connexion se trouve à `/signin` ; ouvrir cette page avant d’accéder aux pages protégées. Les refus d’accès à la création et au tableau de bord utilisent aussi des noms de routes non déclarés (`event_list` sans namespace et `index`).
- **Filtres et navigation** : les champs `search` et `type` sont traités côté serveur mais absents du formulaire de filtrage. Les liens de pagination ne conservent pas les filtres. Le lien « Événements Disponibles » de la barre de navigation pointe vers `#` ; utiliser le bouton d’accueil ou `/events/list/`.
- **Validation des événements** : le modèle définit un contrôle de cohérence des dates, mais les vues de création et de modification n’appellent pas `full_clean()`. La vue d’inscription ne contrôle pas non plus que l’événement est encore à venir.
- **Ressources statiques** : le dossier `static/` et l’image de profil par défaut `static/images/default-profile.png` sont absents. Bootstrap, Font Awesome et Flatpickr dépendent des CDN utilisés dans les templates.

### Configuration du dépôt

La configuration livrée est destinée au développement : `DEBUG=True`, `ALLOWED_HOSTS=[]`, clé Django dans `config/settings.py` et paramètres de connexion SMTP dans `config/info.py`. Ces valeurs doivent être adaptées avant un déploiement ; les identifiants existants ne sont pas reproduits dans cette documentation.

Le fichier nommé `gitignore` ne porte pas le nom `.gitignore` attendu par Git. La base SQLite, des médias et des fichiers `__pycache__` sont déjà suivis dans le dépôt. Aucun fichier de licence n’est fourni.
