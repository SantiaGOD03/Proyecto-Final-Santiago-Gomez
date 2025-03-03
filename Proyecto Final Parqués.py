import random
import time
import os

# Constantes
NUMERO_JUGADORES = 4
NUMERO_FICHAS = 4
TAMANO_TABLERO = 68
SALIDA_FICHAS = 5
TAMANO_LLEGADA = 8
BONUS_CAPTURA = 20
BONUS_LLEGADA = 10

# Códigos de color ANSI
COLORES = {
    0: "\033[91m",  # Rojo
    1: "\033[92m",  # Verde
    2: "\033[94m",  # Azul
    3: "\033[93m",  # Amarillo
    "RESET": "\033[0m",
    "NEGRITA": "\033[1m"
}

# Nombres de los jugadores
NOMBRES_JUGADORES = ["Rojo", "Verde", "Azul", "Amarillo"]

class Ficha:
    def __init__(self, id_jugador, id_ficha):
        self.id_jugador = id_jugador
        self.id_ficha = id_ficha
        self.posicion = -1  # -1 indica en la cárcel
        self.en_recta_final = False
        self.posicion_llegada = -1  # -1 indica que no está en la recta final
        self.terminada = False

    def esta_en_carcel(self):
        return self.posicion == -1 and not self.terminada

    def esta_en_salida(self, tablero):
        return self.posicion == tablero.obtener_posicion_salida(self.id_jugador)

    def mover(self, pasos, tablero):
        if self.esta_en_carcel():
            # Si la ficha está en la cárcel, colocarla en la posición de salida
            self.posicion = tablero.obtener_posicion_salida(self.id_jugador)
            return True
        
        if self.en_recta_final:
            nueva_posicion_llegada = self.posicion_llegada + pasos
            if nueva_posicion_llegada < TAMANO_LLEGADA:
                self.posicion_llegada = nueva_posicion_llegada
                if nueva_posicion_llegada == TAMANO_LLEGADA - 1:
                    self.terminada = True
                return True
            else:
                return False  # No se puede mover, se pasaría de la llegada
        else:
            # Verificar si está a punto de entrar en la recta final
            posicion_actual = self.posicion
            posicion_entrada = tablero.obtener_entrada_llegada(self.id_jugador)
            
            # Calcular distancia a la entrada de la recta final
            distancia_a_entrada = (posicion_entrada - posicion_actual) % TAMANO_TABLERO
            
            if distancia_a_entrada <= pasos:
                # Entrar en la recta final
                pasos_restantes = pasos - distancia_a_entrada
                if pasos_restantes < TAMANO_LLEGADA:
                    self.en_recta_final = True
                    self.posicion_llegada = pasos_restantes
                    self.posicion = -2  # Marcador para "en recta final"
                    return True
                else:
                    return False  # No se puede mover, se pasaría de la llegada
            else:
                # Movimiento normal en el tablero
                nueva_posicion = (posicion_actual + pasos) % TAMANO_TABLERO
                self.posicion = nueva_posicion
                return True
    
    def __str__(self):
        if self.terminada:
            return f"Jugador {self.id_jugador} Ficha {self.id_ficha} (Terminada)"
        elif self.esta_en_carcel():
            return f"Jugador {self.id_jugador} Ficha {self.id_ficha} (En cárcel)"
        elif self.en_recta_final:
            return f"Jugador {self.id_jugador} Ficha {self.id_ficha} (En llegada: {self.posicion_llegada})"
        else:
            return f"Jugador {self.id_jugador} Ficha {self.id_ficha} (Posición: {self.posicion})"

class Tablero:
    def __init__(self):
        self.casillas = [{} for _ in range(TAMANO_TABLERO)]
        # Configurar posiciones de seguro (cada 17 casillas, empezando en 0)
        self.seguros = [0, 17, 34, 51]
        # Configurar salidas (5 casillas después de cada seguro)
        self.salidas = [(s + 5) % TAMANO_TABLERO for s in self.seguros]
        # Configurar entradas a las rectas finales (cada 17 casillas, antes de cada salida)
        self.entradas_llegada = [(s - 1) % TAMANO_TABLERO for s in self.salidas]
    
    def obtener_posicion_salida(self, id_jugador):
        return self.salidas[id_jugador]
    
    def obtener_entrada_llegada(self, id_jugador):
        return self.entradas_llegada[id_jugador]
    
    def es_seguro(self, posicion):
        return posicion in self.seguros
    
    def es_salida(self, posicion):
        return posicion in self.salidas
    
    def agregar_ficha(self, ficha):
        if ficha.posicion >= 0:  # Solo si la ficha está en el tablero principal
            if ficha.posicion not in self.casillas:
                self.casillas[ficha.posicion] = {}
            self.casillas[ficha.posicion][ficha.id_jugador] = self.casillas[ficha.posicion].get(ficha.id_jugador, 0) + 1
    
    def remover_ficha(self, ficha):
        if ficha.posicion >= 0:  # Solo si la ficha está en el tablero principal
            if ficha.posicion in self.casillas and ficha.id_jugador in self.casillas[ficha.posicion]:
                self.casillas[ficha.posicion][ficha.id_jugador] -= 1
                if self.casillas[ficha.posicion][ficha.id_jugador] == 0:
                    del self.casillas[ficha.posicion][ficha.id_jugador]
    
    def hay_bloqueo(self, posicion):
        if posicion < 0:  # Posiciones especiales (cárcel, recta final)
            return False
        
        if posicion not in self.casillas:
            return False
        
        # Verificar si hay dos fichas del mismo jugador en la posición
        for jugador, num_fichas in self.casillas[posicion].items():
            if num_fichas >= 2:
                return True
        
        # Verificar si es seguro o salida con fichas de diferentes jugadores
        if (self.es_seguro(posicion) or self.es_salida(posicion)) and len(self.casillas[posicion]) > 1:
            return True
        
        return False
    
    def obtener_jugadores_en_casilla(self, posicion):
        if posicion < 0 or posicion not in self.casillas:
            return {}
        return self.casillas[posicion]
    
    def reiniciar(self):
        self.casillas = [{} for _ in range(TAMANO_TABLERO)]

class Juego:
    def __init__(self, numero_jugadores=NUMERO_JUGADORES, modo_desarrollador=False):
        self.numero_jugadores = numero_jugadores
        self.modo_desarrollador = modo_desarrollador
        self.tablero = Tablero()
        self.jugadores = []
        self.fichas = []
        self.turno_actual = 0
        self.dados = [0, 0]
        self.pares_consecutivos = 0
        self.ultima_ficha_movida = None
        self.bonus_pendiente = 0
        
        # Inicializar jugadores y fichas
        for i in range(numero_jugadores):
            self.jugadores.append(i)
            for j in range(NUMERO_FICHAS):
                ficha = Ficha(i, j)
                self.fichas.append(ficha)
    
    def limpiar_pantalla(self):
        sistema = platform.system()
        if sistema == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    
    def obtener_fichas_jugador(self, id_jugador):
        return [ficha for ficha in self.fichas if ficha.id_jugador == id_jugador]
    
    def obtener_ficha_por_id(self, id_jugador, id_ficha):
        for ficha in self.fichas:
            if ficha.id_jugador == id_jugador and ficha.id_ficha == id_ficha:
                return ficha
        return None
    
    def lanzar_dados(self):
        if self.modo_desarrollador:
            opcion = input("¿Desea lanzar dados al azar (1) o ingresar valores manualmente (2)? ")
            if opcion == "2":
                dado1 = int(input("Ingrese el valor del primer dado (1-6): "))
                dado2 = int(input("Ingrese el valor del segundo dado (1-6): "))
                self.dados = [dado1, dado2]
                return
        
        self.dados = [random.randint(1, 6), random.randint(1, 6)]
    
    def verificar_pares(self):
        if self.dados[0] == self.dados[1]:
            self.pares_consecutivos += 1
            if self.pares_consecutivos == 3 and self.ultima_ficha_movida:
                print(f"{COLORES[self.turno_actual]}¡Tres pares consecutivos! La última ficha movida regresa a la cárcel.{COLORES['RESET']}")
                self.tablero.remover_ficha(self.ultima_ficha_movida)
                self.ultima_ficha_movida.posicion = -1
                self.ultima_ficha_movida.en_recta_final = False
                self.ultima_ficha_movida.posicion_llegada = -1
                self.pares_consecutivos = 0
            return True
        else:
            self.pares_consecutivos = 0
            return False
    
    def verificar_victoria(self, id_jugador):
        fichas_jugador = self.obtener_fichas_jugador(id_jugador)
        return all(ficha.terminada for ficha in fichas_jugador)
    
    def capturar_ficha(self, posicion, id_jugador):
        # Buscar fichas en la posición que no sean del jugador actual
        for ficha in self.fichas:
            if ficha.posicion == posicion and ficha.id_jugador != id_jugador:
                print(f"{COLORES[id_jugador]}¡El jugador {NOMBRES_JUGADORES[id_jugador]} ha capturado una ficha del jugador {NOMBRES_JUGADORES[ficha.id_jugador]}!{COLORES['RESET']}")
                self.tablero.remover_ficha(ficha)
                ficha.posicion = -1
                ficha.en_recta_final = False
                ficha.posicion_llegada = -1
                return True
        return False
    
    def ficha_puede_moverse(self, ficha, pasos):
        # Si la ficha está en la cárcel, solo puede salir con un 5
        if ficha.esta_en_carcel():
            return pasos == SALIDA_FICHAS
        
        # Si la ficha está en la recta final, asegurarse de que no se pase
        if ficha.en_recta_final:
            return ficha.posicion_llegada + pasos < TAMANO_LLEGADA
        
        # Verificar si hay bloqueos en el camino
        posicion_actual = ficha.posicion
        for i in range(1, pasos + 1):
            posicion_siguiente = (posicion_actual + i) % TAMANO_TABLERO
            
            # Si hay un bloqueo, solo podemos avanzar hasta el bloqueo - 1
            if self.tablero.hay_bloqueo(posicion_siguiente):
                return False
        
        # Verificar si está por entrar a la recta final
        posicion_entrada = self.tablero.obtener_entrada_llegada(ficha.id_jugador)
        distancia_a_entrada = (posicion_entrada - posicion_actual) % TAMANO_TABLERO
        
        if distancia_a_entrada <= pasos:
            # Si entraría a la recta final, verificar que no se pase
            pasos_restantes = pasos - distancia_a_entrada
            return pasos_restantes < TAMANO_LLEGADA
        
        return True
    
    def obtener_movimientos_posibles(self, fichas, valores_dados):
        movimientos = []
        
        # Primero, verificar si hay fichas en la cárcel que pueden salir
        fichas_carcel = [f for f in fichas if f.esta_en_carcel()]
        if fichas_carcel and (SALIDA_FICHAS in valores_dados or sum(valores_dados) == SALIDA_FICHAS):
            # Si hay un 5 en los dados, es obligatorio sacar una ficha
            for ficha in fichas_carcel:
                if SALIDA_FICHAS in valores_dados:
                    idx = valores_dados.index(SALIDA_FICHAS)
                    movimientos.append((ficha, SALIDA_FICHAS, [idx]))
                elif sum(valores_dados) == SALIDA_FICHAS:
                    movimientos.append((ficha, SALIDA_FICHAS, [0, 1]))
            return movimientos
        
        # Verificar movimientos para cada ficha con cada dado
        for ficha in fichas:
            for i, valor in enumerate(valores_dados):
                if self.ficha_puede_moverse(ficha, valor):
                    movimientos.append((ficha, valor, [i]))
            
            # También verificar la suma de los dados
            if len(valores_dados) > 1 and valores_dados[0] != valores_dados[1]:
                suma = sum(valores_dados)
                if self.ficha_puede_moverse(ficha, suma):
                    movimientos.append((ficha, suma, list(range(len(valores_dados)))))
        
        return movimientos
    
    def realizar_movimiento(self, ficha, pasos):
        # Guardar la posición actual para verificar capturas después
        posicion_anterior = ficha.posicion
        
        # Remover la ficha del tablero temporalmente
        self.tablero.remover_ficha(ficha)
        
        # Mover la ficha
        if ficha.esta_en_carcel():
            print(f"{COLORES[ficha.id_jugador]}Sacando ficha {ficha.id_ficha} del jugador {NOMBRES_JUGADORES[ficha.id_jugador]} de la cárcel{COLORES['RESET']}")
        else:
            print(f"{COLORES[ficha.id_jugador]}Moviendo ficha {ficha.id_ficha} del jugador {NOMBRES_JUGADORES[ficha.id_jugador]} {pasos} casillas{COLORES['RESET']}")
        
        puede_moverse = ficha.mover(pasos, self.tablero)
        
        if not puede_moverse:
            print(f"{COLORES[ficha.id_jugador]}¡Movimiento no válido! La ficha no puede moverse {pasos} casillas{COLORES['RESET']}")
            # Si no pudo moverse, restaurar su posición
            if not ficha.esta_en_carcel():
                ficha.posicion = posicion_anterior
                self.tablero.agregar_ficha(ficha)
            return False
        
        # Verificar si ha llegado a la meta
        if ficha.terminada:
            print(f"{COLORES[ficha.id_jugador]}¡La ficha {ficha.id_ficha} del jugador {NOMBRES_JUGADORES[ficha.id_jugador]} ha llegado a la meta!{COLORES['RESET']}")
            # Otorgar bonus por llegar a la meta
            self.bonus_pendiente += BONUS_LLEGADA
            return True
        
        # Agregar la ficha en su nueva posición si no está en la recta final
        if not ficha.en_recta_final:
            # Verificar si hay capturas en la nueva posición
            hay_captura = False
            if not self.tablero.es_seguro(ficha.posicion) and not self.tablero.es_salida(ficha.posicion):
                hay_captura = self.capturar_ficha(ficha.posicion, ficha.id_jugador)
                if hay_captura:
                    # Otorgar bonus por captura
                    self.bonus_pendiente += BONUS_CAPTURA
            
            # Añadir la ficha al tablero en su nueva posición
            self.tablero.agregar_ficha(ficha)
        
        self.ultima_ficha_movida = ficha
        return True
    
    def jugar_turno(self):
        jugador_actual = self.jugadores[self.turno_actual]
        fichas_jugador = self.obtener_fichas_jugador(jugador_actual)
        
        print(f"\n{COLORES[jugador_actual]}{COLORES['NEGRITA']}TURNO DEL JUGADOR {NOMBRES_JUGADORES[jugador_actual]}{COLORES['RESET']}")
        input("Presione Enter para lanzar los dados...")
        
        self.lanzar_dados()
        print(f"Dados: {self.dados[0]} y {self.dados[1]}")
        
        # Verificar si son pares
        es_par = self.verificar_pares()
        
        # Lista para almacenar los valores de los dados disponibles
        valores_dados = self.dados.copy()
        
        # Si hay un bonus pendiente, agregarlo a los valores disponibles
        if self.bonus_pendiente > 0:
            print(f"{COLORES[jugador_actual]}¡Bonus de {self.bonus_pendiente} movimientos disponibles!{COLORES['RESET']}")
            valores_dados.append(self.bonus_pendiente)
            self.bonus_pendiente = 0
        
        while valores_dados:
            self.mostrar_tablero()
            
            # Obtener movimientos posibles
            movimientos_posibles = self.obtener_movimientos_posibles(fichas_jugador, valores_dados)
            
            if not movimientos_posibles:
                print(f"{COLORES[jugador_actual]}No hay movimientos posibles. Perdiendo turno...{COLORES['RESET']}")
                valores_dados = []
                break
            
            # Mostrar movimientos posibles
            print("\nMovimientos posibles:")
            for i, (ficha, pasos, indices_dados) in enumerate(movimientos_posibles):
                dados_usados = [valores_dados[idx] for idx in indices_dados]
                print(f"{i+1}. Mover ficha {ficha.id_ficha} {pasos} casillas usando {dados_usados}")
            
            # Solicitar movimiento al jugador
            seleccion = input("Seleccione un movimiento (o presione Enter para pasar): ")
            if not seleccion:
                valores_dados = []
                break
            
            try:
                seleccion = int(seleccion) - 1
                if 0 <= seleccion < len(movimientos_posibles):
                    ficha, pasos, indices_dados = movimientos_posibles[seleccion]
                    
                    # Realizar el movimiento
                    movimiento_exitoso = self.realizar_movimiento(ficha, pasos)
                    
                    if movimiento_exitoso:
                        # Remover los dados usados
                        indices_dados.sort(reverse=True)
                        for idx in indices_dados:
                            valores_dados.pop(idx)
                    
                    # Verificar victoria
                    if self.verificar_victoria(jugador_actual):
                        return True
                else:
                    print("Selección no válida.")
            except ValueError:
                print("Por favor, ingrese un número válido.")
        
        # Cambiar al siguiente turno si no son pares
        if not es_par:
            self.turno_actual = (self.turno_actual + 1) % self.numero_jugadores
        else:
            print(f"{COLORES[jugador_actual]}¡Dados pares! Tienes otro turno.{COLORES['RESET']}")
        
        return False
    
    def mostrar_tablero(self):
        self.limpiar_pantalla()
        
        # Crear representación del tablero
        ancho = 70
        
        # Imprimir encabezado
        print("=" * ancho)
        print(f"{' PARQUÉS UN ':=^{ancho}}")
        print("=" * ancho)
        
        # Imprimir información del turno actual
        print(f"Turno del jugador: {COLORES[self.turno_actual]}{NOMBRES_JUGADORES[self.turno_actual]}{COLORES['RESET']}")
        print(f"Dados: {self.dados[0]} y {self.dados[1]}")
        print("-" * ancho)
        
        # Imprimir información de cada jugador
        for i in range(self.numero_jugadores):
            fichas_jugador = self.obtener_fichas_jugador(i)
            en_carcel = [f.id_ficha for f in fichas_jugador if f.esta_en_carcel()]
            en_tablero = [(f.id_ficha, f.posicion) for f in fichas_jugador if not f.esta_en_carcel() and not f.en_recta_final and not f.terminada]
            en_llegada = [(f.id_ficha, f.posicion_llegada) for f in fichas_jugador if f.en_recta_final and not f.terminada]
            terminadas = [f.id_ficha for f in fichas_jugador if f.terminada]
            
            print(f"{COLORES[i]}Jugador {NOMBRES_JUGADORES[i]}:{COLORES['RESET']}")
            print(f"  En cárcel: {en_carcel}")
            print(f"  En tablero: {en_tablero}")
            print(f"  En llegada: {en_llegada}")
            print(f"  Terminadas: {terminadas}")
        
        print("-" * ancho)
        
        # Imprimir información de las casillas de seguro y salida
        print("Casillas de seguro:", self.tablero.seguros)
        print("Casillas de salida:", self.tablero.salidas)
        
        # Imprimir información de bloqueos
        bloqueos = []
        for pos in range(TAMANO_TABLERO):
            if self.tablero.hay_bloqueo(pos):
                jugadores = self.tablero.obtener_jugadores_en_casilla(pos)
                bloqueos.append((pos, jugadores))
        
        if bloqueos:
            print("\nBloqueos actuales:")
            for pos, jugadores in bloqueos:
                jugadores_info = ", ".join([f"{COLORES[j]}{NOMBRES_JUGADORES[j]}({n}){COLORES['RESET']}" for j, n in jugadores.items()])
                print(f"  Posición {pos}: {jugadores_info}")
        
        print("=" * ancho)
    
    def jugar(self):
        self.limpiar_pantalla()
        print("""
╔═══════════════════════════════════════════╗
║                PARQUÉS UN                 ║
╚═══════════════════════════════════════════╝
""")
        
        
        # Configurar el juego
        num_jugadores = int(input("Ingrese el número de jugadores (2-4): "))
        while num_jugadores < 2 or num_jugadores > 4:
            num_jugadores = int(input("Número no válido. Ingrese un número entre 2 y 4: "))
        self.numero_jugadores = num_jugadores
        
        # Configurar modo de juego
        modo = input("Seleccione el modo de juego:\n1. Modo normal\n2. Modo desarrollador\nOpción: ")
        self.modo_desarrollador = (modo == "2")
        
        # Inicializar el juego
        self.tablero.reiniciar()
        self.jugadores = list(range(num_jugadores))
        self.fichas = []
        self.turno_actual = 0
        
        for i in range(num_jugadores):
            for j in range(NUMERO_FICHAS):
                ficha = Ficha(i, j)
                self.fichas.append(ficha)
        
        # Loop principal del juego
        juego_terminado = False
        while not juego_terminado:
            victoria = self.jugar_turno()
            if victoria:
                self.mostrar_tablero()
                ganador = self.jugadores[self.turno_actual]
                print(f"\n{COLORES[ganador]}{COLORES['NEGRITA']}¡EL JUGADOR {NOMBRES_JUGADORES[ganador]} HA GANADO!{COLORES['RESET']}")
                juego_terminado = True
            
            time.sleep(1)
        
        print("\nGracias por jugar Parqués UN")
        input("Presione Enter para salir...")

if __name__ == "__main__":
    # Intentar configurar la terminal para mostrar colores en Windows
    if platform.system() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
    
    juego = Juego()
    juego.jugar()