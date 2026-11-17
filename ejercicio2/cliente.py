import grpc
import telemetria_pb2
import telemetria_pb2_grpc

ROJO = "\033[91m"
VERDE = "\033[92m"
AMARILLO = "\033[93m"
RESET = "\033[0m"


def monitorear_camion(stub, id_camion, intervalo):
    print(f"\n=== Suscribiendo a telemetría del camión {id_camion} (intervalo: {intervalo}s) ===")
    peticion = telemetria_pb2.SuscripcionCamion(
        id_camion=id_camion,
        intervalo_segundos=intervalo,
    )

    try:
        for respuesta in stub.TransmitirTelemetria(peticion):
            if respuesta.alerta_critica:
                print(
                    f"{ROJO}[!!! ALERTA CRÍTICA !!!] {respuesta.timestamp} | "
                    f"Camión: {respuesta.id_camion} | Temp: {respuesta.temperatura_celsius}°C "
                    f"(FUERA DE RANGO 2°C-8°C) | GPS: ({respuesta.latitud}, {respuesta.longitud}){RESET}"
                )
            else:
                print(
                    f"{VERDE}[NORMAL]{RESET} {respuesta.timestamp} | "
                    f"Camión: {respuesta.id_camion} | Temp: {respuesta.temperatura_celsius}°C | "
                    f"GPS: ({respuesta.latitud}, {respuesta.longitud})"
                )
        print(f"{AMARILLO}[Cliente] Stream finalizado para {id_camion}.{RESET}")
    except grpc.RpcError as e:
        print(f"{ROJO}[Error gRPC] Código: {e.code()} | Detalle: {e.details()}{RESET}")


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = telemetria_pb2_grpc.MonitorCadenaFrioStub(channel)

        # Prueba 1: Camión inexistente (debe capturar NOT_FOUND)
        monitorear_camion(stub, "CAM-999", 1)

        # Prueba 2: Camión válido con streaming en tiempo real cada 1 segundo
        monitorear_camion(stub, "CAM-001", 1)


if __name__ == "__main__":
    run()
