CRASH_IMPULSO_UMBRAL = 15_000

estado_juego = {
    'ultimo_impulso'   : 0.0,
    'contactos_activos': 0,
}

def registrar_handlers(space, ruedas_ct, terrenos_ct):
    for rueda_ct in ruedas_ct:
        for terreno_ct in terrenos_ct:
            crear_handler(space, rueda_ct, terreno_ct[2])

def crear_handler(space, rueda_ct, terreno_ct):
    
    def begin(arbiter, space, data):
        estado_juego['contactos_activos'] += 1
        #print(estado_juego['contactos_activos'])
        return True

    def post_solve(arbiter, space, data):
        impulso = arbiter.total_impulse.length
        estado_juego['ultimo_impulso'] = impulso
        #print(estado_juego['ultimo_impulso'])

    def separate(arbiter, space, data):
        estado_juego['contactos_activos'] = \
            max(0, estado_juego['contactos_activos'] - 1)
        

    space.on_collision(rueda_ct, terreno_ct, begin=begin,post_solve=post_solve,separate=separate)
