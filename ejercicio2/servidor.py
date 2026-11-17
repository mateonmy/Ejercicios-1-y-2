from concurrent import futures
from datetime import datetime
import random
import time
import grpc
import telemetria_pb2
import telemetria_pb2_grpc

CAMIONES_VALIDOS = {
    "CAM-001": {"lat": -0.180653, "lon": -78.467834},  # Ruta Quito Norte
    "CAM-002": {"lat": -0.229850, "lon": -78.524950},  # Ruta Quito Sur
}


class MonitorCadenaFrioServicer(telemetria_pb2_grpc.MonitorCadenaFrioServicer):
    def TransmitirTelemetria(self, request, context):
        id_camion = request.id_camion.strip().upper()
        intervalo = request.intervalo_segundos if request.intervalo_segundos > 0 else 1

        print(f"[Servidor] Nueva suscripción recibida -> Camión: {id_camion} (cada {intervalo}s)")

        # 1. Validar que el camión exista en el sistema
        if id_camion not in CAMIONES_VALIDOS:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"El camión '{id_camion}' no está registrado en el sistema.")
            return

        lat = CAMIONES_VALIDOS[id_camion]["lat"]
        lon = CAMIONES_VALIDOS[id_camion]["lon"]

        # 2. Emitir flujo continuo (10 lecturas simuladas) usando yield
        for i in range(1, 11):
            if not context.is_active():
                print(f"[Servidor] Cliente desconectado del stream de {id_camion}.")
                break

            # Simular desplazamiento GPS
            lat += random.uniform(-0.0015, 0.0015)
            lon += random.uniform(-0.0015, 0.0015)

            # Simular temperatura (rango normal 2.0°C - 8.0°C, con picos fuera de rango)
            if i in (4, 8):
                temperatura = round(random.choice([random.uniform(0.5, 1.8), random.uniform(8.3, 10.5)]), 2)
            else:
                temperatura = round(random.uniform(2.5, 7.5), 2)

            # 3. Evaluar regla de cadena de frío (< 2.0°C o > 8.0°C)
            alerta = temperatura < 2.0 or temperatura > 8.0
            marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(
                f"[Servidor] Enviando lectura #{i} [{id_camion}] -> "
                f"Temp: {temperatura}°C | Alerta: {alerta}"
            )

            yield telemetria_pb2.LecturaSensor(
                id_camion=id_camion,
                temperatura_celsius=temperatura,
                latitud=round(lat, 6),
                longitud=round(lon, 6),
                timestamp=marca_tiempo,
                alerta_critica=alerta,
            )

            time.sleep(intervalo)

        print(f"[Servidor] Transmisión finalizada para {id_camion}.")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    telemetria_pb2_grpc.add_MonitorCadenaFrioServicer_to_server(
        MonitorCadenaFrioServicer(), server
    )
    puerto = "50051"
    server.add_insecure_port(f"[::]:{puerto}")
    server.start()
    print(f"Servidor MonitorCadenaFrio gRPC escuchando en el puerto {puerto}...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
