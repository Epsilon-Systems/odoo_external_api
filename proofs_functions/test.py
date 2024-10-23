#!/usr/bin/env python3
import datetime

def test_cron():
    try:
        print('----------------------------------------------------------------')
        print(f"Tarea")
        with open(r'C:\dev\odoo_external_api\logs\console.log', 'a') as log_file:
            log_file.write(f"{datetime.datetime.now()}: script ejecutado correctamente")
        print('----------------------------------------------------------------')
    except Exception as e:
        print(f"Error al ejecutar la tarea automática: {e}")
        with open(r'C:\dev\odoo_external_api\logs\console.log', 'a') as log_file:
            log_file.write(f"{datetime.datetime.now()}: error al ejecutar {e}")

if __name__ == "__main__":
    test_cron()
    print('Listo')
    print('Este arroz ya se coció :)')