import config #Para el archivo config y saque las credenciales de ahi
import logging #Para que genere un archivo con los logs

logging.basicConfig(filename='pick_priority.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info('El pedido %s aun no es prioritario', pick_name) #Reemplazas los prints por esta estrucgtura y el log el %s es donde va la info de la variable

#Creas un archivo de configuracion llamado config.py
#y dentro de ese archivo agregas las credenciaes:

dbuser = "will"
dbpassword = "RClTFPNeongrVSko"
oduser = "admin"
odpassword = "9Lh5Z0x*bCqV"

#y agregas las variables del config donde vayan las cedenciales ejemplo:

dbserver = MySQLdb.connect('wonderbrands1.cuwd36ifbz5t.us-east-1.rds.amazonaws.com', config.dbuser, config.dbpassword, local_infile=True)