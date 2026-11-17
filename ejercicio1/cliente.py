import grpc
import pagos_pb2
import pagos_pb2_grpc


def enviar_pago(stub, solicitud):
    print(f"\n--- Enviando Transacción: {solicitud.id_transaccion} ---")
    try:
        respuesta = stub.VerificarTransaccion(solicitud)
        if respuesta.aprobado:
            print(
                f"[APROBADA] Código de autorización: {respuesta.codigo_autorizacion}"
            )
        else:
            print(
                f"[RECHAZADA] Motivo: {respuesta.motivo_rechazo}"
            )
    except grpc.RpcError as e:
        print(f"[Error gRPC] Código: {e.code()} | Detalle: {e.details()}")


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = pagos_pb2_grpc.ValidadorPagosStub(channel)

        # Caso 1: Pago exitoso
        pago_exitoso = pagos_pb2.SolicitudPago(
            id_transaccion="TX-1001",
            numero_tarjeta="4532123456789012",
            monto=250.75,
            codigo_moneda="USD",
            pais_origen="EC",
        )
        enviar_pago(stub, pago_exitoso)

        # Caso 2: Argumento inválido (monto negativo)
        pago_invalido = pagos_pb2.SolicitudPago(
            id_transaccion="TX-1002",
            numero_tarjeta="4532123456789012",
            monto=-50.00,
            codigo_moneda="USD",
            pais_origen="EC",
        )
        enviar_pago(stub, pago_invalido)

        # Caso 3: Tarjeta denegada (inicia con "4000")
        pago_fraude = pagos_pb2.SolicitudPago(
            id_transaccion="TX-1003",
            numero_tarjeta="4000111122223333",
            monto=120.00,
            codigo_moneda="USD",
            pais_origen="US",
        )
        enviar_pago(stub, pago_fraude)

        # Caso 4 (Extra): Monto > $10,000 USD desde país distinto a US/MX
        pago_monto_alto = pagos_pb2.SolicitudPago(
            id_transaccion="TX-1004",
            numero_tarjeta="5105105105105100",
            monto=12500.00,
            codigo_moneda="USD",
            pais_origen="EC",
        )
        enviar_pago(stub, pago_monto_alto)


if __name__ == "__main__":
    run()
