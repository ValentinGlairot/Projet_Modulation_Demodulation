import numpy as np
import soundfile
import pathlib

emplacementFichier="Message.csv"
Fe = 40000
baud = 300
fp1 = 17000
fp2 = 19000

# Conversion Decimal-Binaire
def DecimalVersBinaire(n):
    r=''
    while n>0:
        r+=(str(n%2))
        n=n//2
    while len(r)<8:
        r+='0'
    return r[::-1]

# Encodage Manchester
def EncodageManchester(r):
    messageCode=[]
    for nb in r:
        if nb==1:
            messageCode.append(0)
            messageCode.append(1)
        else:
            messageCode.append(1)
            messageCode.append(0)
    return messageCode

# Modulation ASK
def ModulationASK(signal):
    Ns =int(Fe/baud)
    N =Ns*len(signal)

    M_duplique=np.repeat(signal,Ns)
    t=np.linspace(0,N/Fe,N)

    Porteuse =np.sin(2*np.pi*fp1*t)

    ASK = Porteuse*M_duplique
    return ASK,Porteuse,N,Ns


# Modulation FSK
def ModulationFSK(signal):
    Ns =int(Fe/baud)
    N =Ns*len(signal)

    M_duplique=np.repeat(signal,Ns)
    t=np.linspace(0,N/Fe,N)

    P1 = np.sin(2*np.pi*fp1*t)
    P2 = np.sin(2*np.pi*fp2*t)

    FSK = [] 

    for i in range (0,len(t)):
        
        if M_duplique[i] > 0:
            FSK.append(P1[i])
                
        if M_duplique[i] <= 0:
            
            FSK.append(P2[i])
    return FSK,P1,P2,N,Ns

# Démodulation ASK
def DemodulationASK(signal,Porteuse,Ns):
    Produit=signal*Porteuse
    Res=[]                    
    for i in range(0,N,Ns):
        if np.trapz(Produit[i:i+Ns])>0:
            Res.append(1)
        else:
            Res.append(0)
    return Res

#**************************************************************************************************************************************

# Démodulation FSK
def DemodulationFSK(signal,P1,P2,Ns):
    P1DM=signal*P1
    P2DM=signal*P2
    Res1=[]
    Res2=[]

    for i in range(0,N,Ns):
        Res1.append(np.trapz(P1DM[i:i+Ns]))
        Res2.append(np.trapz(P2DM[i:i+Ns]))
        Res=[]
        for i in range(len(Res1)):
            if abs(Res1[i])-abs(Res2[i])>0:
                Res.append(1)
            else:
                Res.append(0)
    return Res


# Décodage Manchester
def DecodageManchester(signal):
    messageDecode=[]
    for i in range(0,len(signal),2):
        if signal[i]==1 and signal[i+1]==0:
            messageDecode.append(0)
        else:
            messageDecode.append(1)
    return messageDecode

#Conversion Binaire-ASCII
def BinaireVersASCII(message):
    bin_data = ""
    for elem in message:  
        bin_data += str(elem)
    data_reçu =' '
    def BinaryToDecimal(binary):  
        decimal, i, n = 0, 0, 0
        while(binary != 0): 
            dec = binary % 10
            decimal = decimal + dec * pow(2, i) 
            binary = binary//10
            i += 1
        return (decimal)
    for i in range(0, len(bin_data), 8): 
        temp_data = int(bin_data[i+1:i+8])
        decimal_data = BinaryToDecimal(temp_data)
        data_reçu = data_reçu + chr(decimal_data)
    return data_reçu

# Vérification d'erreur
def VerificationErreurs(message):
    matrice=[]
    for mot in message:
        for caractere in mot :
            matrice.append((DecimalVersBinaire(ord(caractere))))
    verificationErreurs=[]
    for caractere in matrice:
        resultat=0
        for bit in caractere:
            resultat+=int(bit)
        verificationErreurs.append(resultat%2)
    for i in range(8):
        resultat=0
        for caractere in matrice:
            resultat+=int(caractere[i])
        verificationErreurs.append(resultat%2)
    return verificationErreurs

# Génération de la trame
def GenerationTrame(expediteur,destinataire):
    extensionFichier=np.array([pathlib.Path(emplacementFichier).suffix])
    message=np.genfromtxt(emplacementFichier,dtype=str)
    verificationErreurs=VerificationErreurs(message)
    trame=np.concatenate([["DEBUT|"],[len(verificationErreurs)-8],["|"],extensionFichier,["|"],[expediteur],["|"],[destinataire],["|"],message,["|"],verificationErreurs,["|FIN"]])
    return trame

# Récupération des composants
def RecuperationComposant(trame,n):
    composant=''
    nbComposant=1
    for caractere in trame:
            if caractere=='|':
                nbComposant+=1
            elif nbComposant==n:
                composant+=caractere
    return composant

#****************************************************************************************************************************************

# Choix de l'expéditeur et du destinataire
expediteur=input("Entrer le nom de l'expéditeur")
destinataire=input("Entrer le nom du destinataire")

trame=GenerationTrame(expediteur,destinataire)

# Conversion en binaire de chaque caractère du message
trameBinaire=[]
for composant in trame:
    for caractere in composant:
        caractereDecimal=ord(caractere)
        caractereBinaire=DecimalVersBinaire(caractereDecimal)
        for n in caractereBinaire:
            trameBinaire.append(int(n))
            
# Encodage du message binaire
trameCode=EncodageManchester(trameBinaire)

while True:
    try:
        nbModulation = int(input("Veuillez entrer un choix valide : 1=ASK 2=FSK "))
        if nbModulation == 1 or nbModulation == 2:
            break  # Sort de la boucle si l'entrée est valide
        else:
            print("Choix non valide. Veuillez entrer 1 pour ASK ou 2 pour FSK.")
    except ValueError:
        print("Veuillez entrer un nombre entier.")

if nbModulation==1:
    # Modulation ASK du message code
    signal,Porteuse,N,Ns=ModulationASK(trameCode)
if nbModulation==2:
    # Modulation FSK du message code
    signal,P1,P2,N,Ns=ModulationFSK(trameCode)
    
# Emission
soundfile.write("Signal.wav",signal,Fe)

# Réception
fichier_audio=soundfile.read("Signal.wav")[0]

# Démodulation du fichier reçu
if nbModulation==1:
    trameDemodule=DemodulationASK(fichier_audio,Porteuse,Ns)
if nbModulation==2:
    trameDemodule=DemodulationFSK(fichier_audio,P1,P2,Ns)
    
# Decodage du signal démodulé
trameDecode=DecodageManchester(trameDemodule)

# Conversion ASCII du message décodé
trameASCII=BinaireVersASCII(trameDecode)

# Affichage du message ASCII
print(trameASCII) 
print("Le message reçu est :", RecuperationComposant(trameASCII,6))

# Vérification d'erreurs
verificationErreurs=VerificationErreurs(RecuperationComposant(trameASCII,6))
nombreErreurs=0
for i in range(len(verificationErreurs)):
    if verificationErreurs[i]!=int(RecuperationComposant(trameASCII,7)[i]):
        nombreErreurs+=1
print("Le système de vérification d'erreurs a détécté",nombreErreurs,"erreur(s).")

# Envoi d'un accusé de réception
AR=["RECEPTION|",destinataire,"|",expediteur,"|REUSSIE"]
ARBinaire=[]
for composant in AR:
    for caractere in composant:
        caractereDecimal=ord(caractere)
        caractereBinaire=DecimalVersBinaire(caractereDecimal)
        for n in caractereBinaire:
            ARBinaire.append(int(n))
ARCode=EncodageManchester(ARBinaire)
if nbModulation==1:
    signal,Porteuse,N,Ns=ModulationASK(ARCode)
if nbModulation==2:
    signal,P1,P2,N,Ns=ModulationFSK(ARCode)
soundfile.write("AR.wav",signal,Fe)
AR_audio=soundfile.read("AR.wav")[0]
if nbModulation==1:
    ARDemodule=DemodulationASK(AR_audio,Porteuse,Ns)
if nbModulation==2:
    ARDemodule=DemodulationFSK(AR_audio,P1,P2,Ns)
ARDecode=DecodageManchester(ARDemodule)
ARASCII=BinaireVersASCII(ARDecode)
print(ARASCII)

print("Le message reçu est :", RecuperationComposant(trameASCII,6))
print("Le système de vérification d'erreurs a détécté",nombreErreurs,"erreur(s).")
print("Accusé de réception :", ARASCII)