from concurrent import futures
import uuid
import grpc
import pagos_pb2
import pagos_pb2_grpc


class ValidadorPagosServicer(pagos_pb2_grpc.ValidadorPagosServicer):
    def VerificarTransaccion(self, request, context):
        print(
            f"[Servidor] Evaluando TX={request.id_transaccion} | "
            f"Tarjeta={request.numero_tarjeta} | Monto={request.monto} {request.codigo_moneda} | "
            f"País={request.pais_origen}"
        )

        # 1. Validar monto > 0 y longitud de tarjeta == 16 dígitos numéricos
        tarjeta_limpia = request.numero_tarjeta.strip()
        if request.monto <= 0 or len(tarjeta_limpia) != 16 or not tarjeta_limpia.isdigit():
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Monto o número de tarjeta inválido")
            return pagos_pb2.ResultadoPago()

        # 2. Validar tarjeta en lista negra (inicia con "4000")
        if tarjeta_limpia.startswith("4000"):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Tarjeta bloquada por fraude")
            return pagos_pb2.ResultadoPago()

        # 3. Regla de negocio: si monto > 10,000 USD, aprobar solo si pais_origen es "US" o "MX"
        if request.monto > 10000 and request.pais_origen.upper() not in ("US", "MX"):
            return pagos_pb2.ResultadoPago(
                aprobado=False,
                codigo_autorizacion="",
                motivo_rechazo="Rechazada por política de fraude: monto > $10,000 fuera de US/MX",
            )

        # 4. Transacción aprobada
        codigo_auth = f"AUTH-{uuid.uuid4().hex[:8].upper()}"
        return pagos_pb2.ResultadoPago(
            aprobado=True,
            codigo_autorizacion=codigo_auth,
            motivo_rechazo="",
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pagos_pb2_grpc.add_ValidadorPagosServicer_to_server(
        ValidadorPagosServicer(), server
    )
    puerto = "50051"
    server.add_insecure_port(f"[::]:{puerto}")
    server.start()
    print(f"Servidor ValidadorPagos gRPC escuchando en el puerto {puerto}...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
