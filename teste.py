from datetime import datetime, timedelta
import pause


data_inicio = datetime.now() + timedelta(hours=3, minutes=5)

print( data_inicio.strftime('%Y-%m-%dT%H:%M:%S.000Z' ))

hora_inicio = datetime.strptime('2024-02-12T20:22:00Z', '%Y-%m-%dT%H:%M:00Z')

hora_inicio_2 = datetime.strptime('2024-02-12T20:45:00Z', '%Y-%m-%dT%H:%M:00Z')

print( hora_inicio > hora_inicio_2)

pause.until(hora_inicio)

print('saiu do pause')


# 2024-02-11T15:36:24.000Z
# 2024-02-11T15:44:57.000Z