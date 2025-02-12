# supdevinci-tp-ia réalisé par Victor NOURISSON et Loucas TOUGERON

## Lancement de l'application

### Prérequis

Avant de lancer l'application, assurez-vous d'avoir **Streamlit** installé sur votre machine. Si ce n'est pas encore fait, vous pouvez l'installer via la commande suivante :

```bash
pip3 install streamlit
```

### Démarrer l'application
Une fois l'installation terminée, vous pouvez lancer l'application en exécutant la commande suivante dans votre terminal :
```bash
streamlit run app.py
```
Vous devriez voir un message similaire à celui-ci dans votre console :
```bash
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:XXXX
  Network URL: http://XXX.XXX.X.XXX:XXXX
```
Cliquez sur l'une des deux URLs pour ouvrir l'application dans votre navigateur.


## Fonctionnement de l'application

### Configurer l'environnement
Une fois arrivé sur l'application, dans le menu à gauche, cliquez sur le bouton **"Charger depuis .env"** et appuyez sur le bouton **"Valider"**, vous devriez obtenir ce résultat :

![image](https://github.com/user-attachments/assets/b052d9b9-204e-4188-9dc6-1830a571fe03)

### Transférer une image
Dans la partie **"Transférer un fichier"**, déposez ou sélectionnez une image pour l'analyser.
#### Si l'image est appropriée, vous devriez voir ce résultat :

![image](https://github.com/user-attachments/assets/2f643b22-d89a-4edf-a85d-ae7706e54b4f)

#### Si l'image n'est pas appropriée, vous obtiendrez ce résultat :

![image](https://github.com/user-attachments/assets/6890313c-220d-4f56-b75a-b22bb12f3171)

### Transférer une vidéo
Dans la partie **"Transférer un fichier"**, déposez ou sélectionnez une vidéo pour l'analyser.
Après quelques secondes de traitement, vous devriez obtenir ce résultat :

![image](https://github.com/user-attachments/assets/0b8785f9-a1b4-48bf-b5e2-3b60c7185c49)

