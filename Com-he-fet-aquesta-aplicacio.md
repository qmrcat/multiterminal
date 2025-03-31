# Com s'ha fet aquesta aplicació

Aquesta aplicació s’ha fet, utilitzant la intel·ligència artificial en pràcticament 99,5% del seu codi, necessitava una aplicació per tenir agrupats els diferents terminals pels projectes que faig amb Node.js i amb JavaScript, i no tenir diverses finestres obertes

Aclariment, el meu coneixement de Python podem dir que és menor de dos, però tinc una experiència d'informàtic de més de 35 anys, ho vull deixar clar, perquè si no tens experiència informàtica no és possible de fer aplicacions una mica complexes amb l'ajuda d'una IA, el fet que s’hagi fet amb Python, ho va decidir la mateixa intel·ligència artificial. 

Aquesta aplicació amb Python, està totalment feta amb IA, el primer intent es va fer amb Claude 3.7 Sonnet amb raonament activat, el primer indicador (prompt), va ser aquest:

    "Voldria una aplicació per a Windows que tingui incorporat a dins finestres on en cada finestra tingui obert un terminal de Windows". 

En va fer una versió web simulant una terminal, li vaig donar una nova indicació:

    "Però ha de ser una aplicació que es pugui executar al Windows, no una web".

Em va fer una versió prou correcta, però no acabava de funcionar perquè li faltava algunes dependències, després de batalla en instal·lar les dependències i molts indicacions  utilitzades, al final vaig aconseguir una aplicació que s'adaptava al que jo inicialment volia.

Aquí us deixo, les indicacions que vaig utilitzar per fer l'aplicació,

    - Voldria una aplicació per a Windows que tingui incorporat a dins finestres on en cada finestra tingui obert un terminal de Windows. 

    - Però ha de ser una aplicació que es pugui executar al Windows, no una web.

    - Em dona aquest error en intentar actualitzar 'pip'

    - Aquest son els missatges que surten,
      WARNING: Ignoring invalid distribution -p (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution -p (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution -ip (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution - (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution -p (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution -p (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution -ip (c:\python39\lib\site-packages)
      WARNING: Ignoring invalid distribution - (c:\python39\lib\site-packages)
      Requirement already satisfied: pip in c:\python39\lib\site-packages (21.1.3)
      ...
      ...
      ...
      WARNING: You are using pip version 21.1.3; however, version 25.0.1 is available.
      You should consider upgrading via the 'C:\Python39\python.exe -m pip install --upgrade pip' command.

    - No puc accedir dins del terminal per executar comandes del sistema

    - Podries afegir que es pugui modificar el nom de la terminal

    - Ara en clicar el botó de "Nou terminal" es tanca l'aplicació

    - Continua el problema al fer nou terminal, l'error que surt es aquest,
    Traceback (most recent call last):
    File "C:\Users\jmira\Documents\Projectes\ProjectesPython\mutiTerminals\mutiTerm.py", line 223, in add_terminal
    terminal = TerminalWindow(self, title=title)
    ...
    ...
    ...
    Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags()): argument 1 has unexpected type 'bool'

    - Dins la finestra del terminal em surten aquests caràcters,
    [3m[1m[34mÔëê[39m[22m[23m tailwindcss [34mv4.0.9[39m
    Com ho podríem arreglar


    - Surt aquest error,
    Traceback (most recent call last):
    File "C:\Users\jmira\Documents\Projectes\ProjectesPython\mutiTerminals\mutiTerm.py", line 324, in <module>
    main()
    ...
    ...
    ...
    ine 50, in init
    self.process.setEnvironment(env)
    AttributeError: 'QProcess' object has no attribute 'setEnvironment'


    - Ara surt dins del terminal les lletres separades per un espai, per exemple,
    C : \ U s e r s \ j u s e r \ D o c u m e n t s \ P r o j e c t e s

    - Seria possible de tenir un històric de les comandes de cada terminal que hem fet, per exemple, en clicar la fletxa amunt que surti l'anterior o fletxa avall el següent.

    - Pots afegir el Ctrl+c per interrompre l'execució d'una comanda a un terminal i també el 'cls' o 'clear per netejar la finestra del terminal.

    - Pots arreglar l'espai excessiu de l'ària de dalt.

    - El control C no funciona surt al terminal '^C', però no interromp l'execució.

    - Quan es reinicia el terminal amb Ctrl+C ja no executa cap comanda més.

    - Ara amb aquest canvi no interromp l'execució, surt el '^C' al terminal però no interromp.

    -
    [Terminal-servidor]
    cls
    cd "C:\Users\juser\Documents\Projectes\node-projecte\compra"
    npm run dev
    [Terminal-tailwindcss]
    cls
    cd "C:\Users\juser\Documents\Projectes\node-projecte\compra"
    npx @tailwindcss/cli -i ./client/input.css -o ./client/css/styles.css --watch
    [Terminal-cmd]
    cd "C:\Users\juser\Documents\Projectes\node-projecte\compra"
    Voldria afegir uns fitxers d'execució com el que té posar de mostra que obri un terminal [Terminal-servidor] 
    i executi les comandes que té cada grup, per aquest exemple, 'cls', després 'cd "C:\Users\juser\Documents\Projectes\node-projecte\compra"' i el següent 'npm run dev', i després que obrir un nou terminal [Terminal-tailwindcss]... Els fitxers estarien en el mateix directori del fitxer "multi_terminal.py" el podríem passar com a paràmetre en executar-lo, per exemple "python multi_terminal.py projecte2.config"

    ! Nota: ara ja comença a sortir l'avís de començar a superar els límits, "Claude hit the max length for a message and has paused its response. You can write Continue to keep the chat going.", "Claude ha arribat a la longitud màxima d'un missatge i ha posat en pausa la seva resposta. Pots escriure Continua per mantenir el xat.".

    - Continua

    - Podries fer un README.md per penjar-ho a Github del que fa aquesta aplicació

    - Crea la LICENSE

    - Podries fer un prompt de tal manera que pugui continuar l'ampliació d'aquesta aplicació en un altre xat, gràcies.

    - Quan hi ha més de dos terminals el tercer i quart si està obert es poden posar a sota del primer i segon, potser es podria moure els terminals lliurement.

    - Ara executo l'aplicació i no surt res

! Nota: segon avis.

    -Continue

! Nota: aquí li demano que continuï des d'on s'ha tallat, perquè si no entraríem en un bucle talls i ja no podríem seguir.

    - S'ha tallat des d'aquesta funció, "def terminal_dropped(self, source_id, target_id):", pots continuar des d'aquest punt.

----

Com he dit, és totalment funcional, però com que veia que Claude començava a esgotar el context, vaig decidir de canviar d'IA i vaig provar el nou model de Gemini la versió 2.5 Pro Experimental 03-05, que segons deien era molt millor, per desgràcia vaig perdre tot el que havia generat perquè no tenia, cap sessió oberta i en tancar el navegador es va perdre, però llavor vaig, obrir sessió a Google AI Studio, li vaig passar el fitxer que ja tenia generats, cal dir que aquesta versió em va agrada més que la feta per Claude Sonnet, 


Aquí us deixo les indicacions que li vaig fer a Gemini, després de pujar els fitxers,

    - Tinc aquesta aplicació i vull fer algunes modificacions.

    - Quan faig Control + C no cancel·là el procés que sesta fent en la terminal.

    - Com podria fer un executable d'aquesta aplicació.

    - Quan utilitzes el Ctrl+C es tanca el terminal, es podria fer que torni ha estat disponible, gràcies.


    -
    Ara surt aquest errors,
    Carregant tema des de: C:\Users\juser\Documents\Projectes\ProjectesPython\mutiTerminals\multiterminal\themes\default.qss
    Font per defecte detectada: Consolas
    Carregant l'últim layout: C:/Users/juser/Documents/Projectes/ProjectesPython/mutiTerminals/multiterminal/esunaprova.json
    Tancant terminals actuals per carregar layout...
    Carregant 3 terminals del layout...
    ...
    ...
    ...
    command_input.interrupt_signal.connect(terminal_widget.send_interrupt)
    AttributeError: 'TerminalWidget' object has no attribute 'send_interrupt'
    QProcess: Destroyed while process ("cmd.exe") is still running.

! Nota: Anteriorment, vaig cometre un error d'indentació a un escript de Python.

    - Tenies raó estava malament indentat, però ara en executar Ctrl+C es tanca l'aplicació i dona aquest avís,

        Senyal CTRL_C_EVENT enviat amb èxit.
        Traceback (most recent call last):
        File "C:\Users\juser\Documents\Projectes\ProjectesPython\mutiTerminals\multiterminal\terminal_widget.py", line 170, in _handle_output
        def _handle_output(self):
        KeyboardInterrupt


    -
    Ara surt aquest errors,
    Tancant terminals actuals per carregar layout...
    Carregant 3 terminals del layout...
    Configurant modificador per afegir CREATE_NEW_PROCESS_GROUP...
    Traceback (most recent call last):
    ...
    ...
    ...
    self._process.setCreateProcessArgumentsModifier(modify_startup_info)
    AttributeError: 'QProcess' object has no attribute 'setCreateProcessArgumentsModifier'


    - No hem tingut sort, en fer Ctrl+C, s'ha tancat l'aplicació,
    Traceback (most recent call last):
    File "C:\Users\juser\Documents\Projectes\ProjectesPython\mutiTerminals\multiterminal\terminal_widget.py", line 203, in _handle_output
    def _handle_output(self):
    KeyboardInterrupt


    - He actualitzat PyQt5,
    Requirement already satisfied: PyQt5 in c:\python39\lib\site-packages (5.15.11)
    Requirement already satisfied: PyQt5-sip<13,>=12.15 in c:\python39\lib\site-packages (from PyQt5) (12.17.0)
    Requirement already satisfied: PyQt5-Qt5<5.16.0,>=5.15.2 in c:\python39\lib\site-packages (from PyQt5) (5.15.2)
    Ara quins canvis hem de fer?

! Nota: A partir d'aquest punt Gemini, va entrar en bucle en fer-me, desinstal·lar i instal·lar versions de dependències, i no hi havia manera d'en sortint-se, vaig pensar que tocava aprendre més Pythom per continuar jo el projecte, però en aquest moment d'una petita frustració, vaig fer la pensada de fer el mateix que havia fet amb Gemini 2.5, era fer-ho a Claude Sonnet 3.7, li vaig passar els fitxers generats per Gemini a Claude, aquí us deixo les indicacions després de pujar els fitxers.

! Nota: Mentre utilitzava Gemini, com que estàvem en un bucle, vaig decidir de reinstal·lar Python a l'ultima versió i les dependències, per si era un error d’instal·lació corrupte, però no va ser així.

    -
    Tinc aquests scripts, i tinc aquests errors en l'execució de main.py
    Traceback (most recent call last):
    File "C:\Users\juser\Documents\Projectes\ProjectesPython\mutiTerminals\multiterminal\main.py", line 45, in <module>
    main()
    ~~~~^^
    File "C:
    ...
    ...
    ...
    Tinc aquestes dependències instal·lades,
    Package Version
    --------- -------
    ansi2html 1.9.2
    pip 25.0.1
    PyQt5 5.15.11
    PyQt5-Qt5 5.15.2
    PyQt5_sip 12.17.0
    La versió de Python és la, Python 3.13.2


    -
    Ara en fer Ctrl+C, tanca l'aplicació i no el procés que s'està executant a la terminal, en aquest cas un servidor web amb node, i surt aquest error,
    Traceback (most recent call last):
    File "C:\Users\juser\Documents\Projectes\ProjectesPython\mutiTerminals\multiterminal\terminal_widget.py", line 395, in send_interrupt
    print("Senyal CTRL_C_EVENT enviat amb xit.")
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    KeyboardInterrupt

    -Amb Aquestes modificacions no Intentant enviar interrupció al procés (PID: 22476)...
    Enviant caràcter Ctrl+C (\x03)...
    El procés continua en execució després de la interrupció.


    -Torna a tancar l'aplicació, et passo tot el que surt a la consola, des d'on es crida main.py,

    Carregant tema des de: C:\Users\jmira\Documents\Projectes\ProjectesPython\mutiTerminals\multiterminal\themes\default.qss
    Font per defecte detectada: Consolas
    ...
    ...
    ...
    line 526, in checkand_try_alternate_interrupt
    print("Senyal CTRL_C_EVENT enviat.")
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    KeyboardInterrupt

    - Ara no es tanca l'aplicació, però no cancel·la els processos, surt aquest missatge dins de la terminal, però no tanca res, "Per aturar el servidor: Escriu .exit o prem Ctrl+C directament."

    - Podries fer una opció al menú per veure els processos que s'estan executant en cada terminal.

    - Quan es crida per veure els processos l'aplicació es queda com a congelada, podries posar algun avís dient que s'està treballant, per altra banda, quan surt la finestra per escollir el terminal i veure els processos surten tots aquests errors.

    - Es podria veure solament els que estan relacionats amb l'aplicació, i quan surt la graella dels processos que no l'actualitzi, perquè fa un efecte molest en moure la graella.

    - Podries posar el color dels textos més fosc, pràcticament no es veuen bé

    - Per fer un executable d'aquesta aplicació, m'ho pots explicar

    - Els fitxers layout (.json) no voldria que estiguessin inclosos a l'executable

    - En intentar obrir la carpeta de layouts surt un avis, "No s'ha pogut obrir la carpeta de layouts: 'MainWindows' objecte has no atribute 'layouts_dir'

    - Com s'utilitza l'Inno Setup

    - A on genera el fitxer d'instal·lació Inno Setup

    -Vull pujar aquest projecte a Github, em pots fer les indicacions, també podries fer el README.md explicant que fa, com utilitzar l'aplicació, com instal·lar Python i les dependències que necessita, executar l'aplicació amb Python, també com generar un executable, també genera la LICENSE.md

La ultima indicació ha sigut demanar-li a la IA que creia ella que li faltava a l’aplicació per millorar-la 

    -“Que creus que pot faltar en aquesta aplicació per millorar-la.”
    Aquesta ha sigut la resposta,

        Idees per millorar MultiTerminal
        Aquí tens una llista de millores potencials que podrien fer l'aplicació encara més útil i atractiva:
        Millores de Funcionalitat
            Suport per a més tipus de terminal
                Afegir suport per PowerShell, Bash de WSL, i altres shells
                Permetre configurar el tipus de terminal per defecte
            Vista dividida
                Implementar la capacitat de dividir la finestra en múltiples panells (horitzontal/vertical)
                Veure múltiples terminals simultàniament en una mateixa pantalla
            Autocompleció de comandes
                Implementar suggeriments basats en comandes prèvies
                Autocompletar noms de fitxers i directoris
            Execució paral·lela
                Executar la mateixa comanda a múltiples terminals simultàniament
                Opció per sincronitzar entrada entre terminals seleccionats
            Cerca en la sortida
                Afegir funció de cerca dins de la sortida del terminal
                Opció per ressaltar coincidències
            Millor integració amb Git
                Visualitzar més informació de Git (canvis pendents, etc.)
                Afegir funcionalitats bàsiques de Git a la interfície

        Millores d'Interfície
            Més temes i personalització
                Biblioteca ampliada de temes predefinits
                Més opcions de personalització (transparència, estils de cursor, etc.)
            Sistema de notificacions
                Alertes visuals quan un procés finalitza
                Notificacions del sistema per processos llargs
            Perfils de terminal
                Configuracions predefinides per a diferents tipus de tasques
                Opció per canviar ràpidament entre perfils
            Mode compacte
                Interfície minimalista que ocupa menys espai
                Opció per ocultar la barra de menú quan no s'utilitza

        Millores Tècniques
            Actualitzacions automàtiques
                Sistema per detectar i instal·lar actualitzacions
                Notes de versió integrades
            Mode portable
                Versió que funcioni des d'un USB sense necessitat d'instal·lació
                Configuració guardada localment amb l'aplicació
            Suport multiplatforma
                Adaptació per funcionar a Linux i macOS
                Configuració específica per a cada plataforma
            Sistema de plugins
                Arquitectura extensible per afegir funcionalitats
                Marketplace de plugins comunitaris
            Integració amb serveis
                Connexió directa a servidors remots (SSH)
                Integració amb serveis cloud (Azure, AWS, GCP)

        Millores Específiques pels Usuaris
            Gestor avançat de processos
                Monitoratge de recursos per procés (CPU/Memòria)
                Gràfics d'ús de recursos en temps real
            Gestor de tasques programades
                Programar comandes per executar-se a hores específiques
                Guardar i gestionar tasques recurrents
            Opció de compartir terminals
                Exportar/importar sessions completes entre usuaris
                Opció per col·laboració en temps real (futur avançat)
            Millor gestió de l'historial
                Historial persistent entre sessions
                Cerca i filtrat en l'historial de comandes


Per finalitzar, he quedat molt satisfet de com ha quedat l’aplicació i el que es pot arribar ha fer amb la intel·ligència artificial, cal dir que he tardat dos dies en realitzar-la.






