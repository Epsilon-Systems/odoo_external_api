from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from pprint import pprint
from email import encoders
from tqdm import tqdm
import time
import json
import jsonrpc
import jsonrpclib
import random
import urllib.request
import getpass
import http
import requests
import logging
import zipfile
import socket
import os
import locale
import xmlrpc.client
import base64
import openpyxl
import xlrd
import pandas as pd
import MySQLdb
import mysql.connector
import smtplib
import ssl
import email
import datetime

print('================================================================')
print('BIENVENIDO AL PROCESO DE NOTAS DE CRÉDITO PARA MARKETPLACES')
print('================================================================')
print('SCRIPT DE CREACIÓN DE NOTAS DE CRÉDITO PARA FACTURAS GLOBALES')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
config_file_name = r'C:\Dev\wb_odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['odoo']
def get_psql_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['psql']
def get_email_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['email']
def reverse_invoice_global_meli():
    # Obtener credenciales
    odoo_keys = get_odoo_access()
    psql_keys = get_psql_access()
    email_keys = get_email_access()
    # odoo
    server_url = odoo_keys['odoourl']
    db_name = odoo_keys['odoodb']
    username = odoo_keys['odoouser']
    password = odoo_keys['odoopassword']
    # correo
    smtp_server = email_keys['smtp_server']
    smtp_port = email_keys['smtp_port']
    smtp_username = email_keys['smtp_username']
    smtp_password = email_keys['smtp_password']

    print('----------------------------------------------------------------')
    print('NOTAS DE CRÉDITO GLOBALES MELI')
    print('----------------------------------------------------------------')
    print('Conectando API Odoo')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
    uid = common.authenticate(db_name, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
    print('Conexión con Odoo establecida')
    print('----------------------------------------------------------------')
    print('Conectando a Mysql')
    # Connect to MySQL database
    mydb = mysql.connector.connect(
        host=psql_keys['dbhost'],
        user=psql_keys['dbuser'],
        password=psql_keys['dbpassword'],
        database=psql_keys['database']
    )
    mycursor = mydb.cursor()
    print('----------------------------------------------------------------')
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')
    #GLOBALES MELI
    mycursor.execute("""SELECT c.name,
                               b.id 'account_move_id',
                               b.name/*,
                               ifnull(d.order_id, dd.pack_id) 'order_id_or_pack_id',
                               b.amount_total 'total_factura',
                               b.amount_untaxed 'subtotal_factura',
                               ifnull(d.refunded_amt, dd.refunded_amt) 'ml_refunded_amount',
                               ifnull(d.payment_date_last_modified, dd.payment_date_last_modified) 'payment_date_last_modified',
                               b.invoice_partner_display_name 'cliente',
                               'GLOBAL' as type,
                               'MERCADO LIBRE' as marketplace*/
                        FROM somos_reyes.odoo_new_account_move_aux b
                        LEFT JOIN odoo_new_sale_order c
                        ON SUBSTRING_INDEX(SUBSTRING_INDEX(invoice_ids, ']', 1), '[', -1) = b.id
                        LEFT JOIN (SELECT a.order_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(paid_amt) 'paid_amt', SUM(refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                                   FROM ml_order_payments a
                                   LEFT JOIN ml_order_update b
                                   ON a.order_id = b.order_id
                                   WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '2023-11-01' AND date(payment_date_last_modified) <= '2023-11-30'
                                   GROUP BY 1) d
                        ON c.channel_order_id = d.order_id
                        LEFT JOIN (SELECT a.pack_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(b.paid_amt) 'paid_amt', SUM(b.refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                        FROM ml_order_update a
                        LEFT JOIN ml_order_payments b
                        ON a.order_id = b.order_id
                        WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '2023-11-01' AND date(payment_date_last_modified) <= '2023-11-30'
                        GROUP BY 1) dd
                        ON c.yuju_pack_id = dd.pack_id
                        LEFT JOIN (SELECT distinct invoice_origin FROM odoo_new_account_move_aux WHERE name like '%RINV%') e
                        ON c.name = e.invoice_origin
                        WHERE (d.order_id is not null or dd.pack_id is not null)
                        AND e.invoice_origin is null
                        AND invoice_partner_display_name = 'PÚBLICO EN GENERAL'
                        AND (ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total > 1 OR ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total < -1)
                        AND (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total > 1 OR ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total < -1)
                        AND ((ifnull(d.refunded_amt, dd.refunded_amt) - c.amount_total < 1 AND ifnull(d.refunded_amt, dd.refunded_amt) - c.amount_total > -1)
                        OR (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - c.amount_total < 1
                        AND ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - c.amount_total > -1))
                        AND c.name not in ('SO2156130', 'SO2258628', 'SO2309915', 'SO2345917', 'SO2379557', 'SO2438006', 'SO2441167', 'SO2440908',
                                           'SO2227411', 'SO2211148', 'SO2294013', 'SO2292733', 'SO2331845', 'SO2341306', 'SO2344209', 'SO2382497',
                                           'SO2429302', 'SO2447352', 'SO2180933', 'SO2160921', 'SO2193531', 'SO2196161', 'SO2257178', 'SO2291531',
                                           'SO2404117', 'SO2408802', 'SO2409630', 'SO2181047', 'SO2193506', 'SO2222257', 'SO2318594', 'SO2336050',
                                           'SO2350416', 'SO2389164', 'SO2452792', 'SO2233523', 'SO2249534', 'SO2269905', 'SO2391427', 'SO2407764', 'SO2130854', 'SO2186141', 'SO2215717', 'SO2225194', 'SO2247974', 'SO2358118', 'SO2395441', 'SO2098756', 'SO2131503', 'SO2187344', 'SO2172413', 'SO2146783', 'SO2149487', 'SO2169189', 'SO2190432', 'SO2212592', 'SO2329358', 'SO2383170', 'SO2441203', 'SO2190052', 'SO2211244', 'SO2228530', 'SO2328248', 'SO2334096', 'SO2449524', 'SO2101577', 'SO2217178', 'SO2230709', 'SO2266975', 'SO2429462', 'SO2450015', 'SO2148993', 'SO2192311', 'SO2187012', 'SO2267018', 'SO2264050', 'SO2306080', 'SO2332212', 'SO2367508', 'SO2421982', 'SO2136369', 'SO2175959', 'SO2175337', 'SO2180155', 'SO2257968', 'SO2256128', 'SO2286504', 'SO2450282', 'SO2143861', 'SO2139678', 'SO2157698', 'SO2228031', 'SO2245253', 'SO2332623', 'SO2388433', 'SO2160410', 'SO2191090', 'SO2312232', 'SO2315852', 'SO2352230', 'SO2372479', 'SO2413327', 'SO2404195', 'SO2115077', 'SO2139008', 'SO2183958', 'SO2176284', 'SO2122818', 'SO2285974', 'SO2333345', 'SO2375798', 'SO2402651', 'SO2417347', 'SO2094430', 'SO2142682', 'SO2262882', 'SO2256782', 'SO2313264', 'SO2276890', 'SO2291148', 'SO2333205', 'SO2393415', 'SO2411534', 'SO2426519', 'SO2447540', 'SO2158124', 'SO2228265', 'SO2392117', 'SO2421224', 'SO2116698', 'SO2189115', 'SO2268148', 'SO2269463', 'SO2320736', 'SO2349619', 'SO2131373', 'SO2183046', 'SO2257853', 'SO2235291', 'SO2320590', 'SO2437075', 'SO2423002', 'SO2115037', 'SO2223325', 'SO2216918', 'SO2193623', 'SO2287121', 'SO2318543', 'SO2348367', 'SO2419271', 'SO2446635', 'SO2191116', 'SO2220176', 'SO2265501', 'SO2268442', 'SO2317898', 'SO2422848', 'SO2451996', 'SO2105091', 'SO2114462', 'SO2293840', 'SO2123414', 'SO2089912', 'SO2236930', 'SO2252310', 'SO2242940', 'SO2156103', 'SO2152687', 'SO2270814', 'SO2297409', 'SO2377024', 'SO2351793', 'SO2110085', 'SO2178094', 'SO2203342', 'SO2348646', 'SO2408349', 'SO2420756', 'SO2108034', 'SO2223787', 'SO2347452', 'SO2367751', 'SO2386907', 'SO2384513', 'SO2208084', 'SO2251967', 'SO2296884', 'SO2396983', 'SO2169049', 'SO2241149', 'SO2280726', 'SO2357224', 'SO2096028', 'SO2136019', 'SO2210640', 'SO2301015', 'SO2369541', 'SO2431423', 'SO2446388', 'SO2156428', 'SO2207977', 'SO2207701', 'SO2207186', 'SO2226219', 'SO2266740', 'SO2437370', 'SO2435211', 'SO2104659', 'SO2148679', 'SO2226272', 'SO2262876', 'SO2271509', 'SO2224101', 'SO2331809', 'SO2108299', 'SO2135932', 'SO2177381', 'SO2293747', 'SO2406735', 'SO2177626', 'SO2181513', 'SO2195233', 'SO2412541', 'SO2404857', 'SO2381534', 'SO2427845', 'SO2415190', 'SO2112144', 'SO2252123', 'SO2279328', 'SO2289018', 'SO2288674', 'SO2296234', 'SO2374224', 'SO2394230', 'SO2419127', 'SO2153733', 'SO2192534', 'SO2223032', 'SO2267251', 'SO2270751', 'SO2314248', 'SO2382153', 'SO2170417', 'SO2234104', 'SO2240305', 'SO2439971', 'SO2448991', 'SO2107158', 'SO2147786', 'SO2164955', 'SO2390885', 'SO2387123', 'SO2448981', 'SO2063060', 'SO2284932', 'SO2442663', 'SO2106913', 'SO2210867', 'SO2206022', 'SO2268672', 'SO2294292', 'SO2313316', 'SO2418058', 'SO2426750', 'SO2118984', 'SO2173142', 'SO2250698', 'SO2281200', 'SO2381973', 'SO2441437', 'SO2431269', 'SO2102941', 'SO2173114', 'SO2138834', 'SO2188176', 'SO2240613', 'SO2280337', 'SO2327795', 'SO2410647', 'SO2417512', 'SO2190997', 'SO2089227', 'SO2194761', 'SO2208513', 'SO2216036', 'SO2441568', 'SO2407563', 'SO2165028', 'SO2220914', 'SO2256273', 'SO2413701', 'SO2444231', 'SO2108783', 'SO2138033', 'SO2137975', 'SO2173492', 'SO2268064', 'SO2328653', 'SO2191265', 'SO2229888', 'SO2260453', 'SO2262159', 'SO2279432', 'SO2306883', 'SO2407505', 'SO2451267', 'SO2451246', 'SO2156785', 'SO2091651', 'SO2218354', 'SO2354573', 'SO2432134', 'SO2129866', 'SO2216753', 'SO2272795', 'SO2304838', 'SO2282632', 'SO2363715', 'SO2369835', 'SO2112369', 'SO2136546', 'SO2229900', 'SO2215643', 'SO2273281', 'SO2313414', 'SO2399599', 'SO2121872', 'SO2123539', 'SO2195420', 'SO2322726', 'SO2293162', 'SO2331981', 'SO2417858', 'SO2399620', 'SO2097177', 'SO2094940', 'SO2110492', 'SO2243315', 'SO2246285', 'SO2309817', 'SO2366153', 'SO2163636', 'SO2092350', 'SO2226660', 'SO2270836', 'SO2280488', 'SO2286973', 'SO2290646', 'SO2406379', 'SO2446244', 'SO2106668', 'SO2125669', 'SO2186299', 'SO2169723', 'SO2210405', 'SO2257939', 'SO2373918', 'SO2427165', 'SO2421746', 'SO2137821', 'SO2271190', 'SO2312336', 'SO2344881', 'SO2372639', 'SO2382885', 'SO2156311', 'SO2202765', 'SO2220773', 'SO2275661', 'SO2314870', 'SO2425190', 'SO2422785', 'SO2456796', 'SO2098538', 'SO2181388', 'SO2166367', 'SO2259598', 'SO2228632', 'SO2278665', 'SO2336045', 'SO2454561', 'SO2090340', 'SO2208255', 'SO2228561', 'SO2230885', 'SO2294124', 'SO2371043', 'SO2439490', 'SO2145870', 'SO2311565', 'SO2330189', 'SO2363668', 'SO2452101', 'SO2113668', 'SO2117798', 'SO2165495', 'SO2185818', 'SO2190462', 'SO2114489', 'SO2154402', 'SO2167291', 'SO2441253', 'SO2107208', 'SO2268844', 'SO2323085', 'SO2317907', 'SO2266117', 'SO2454556', 'SO2096137', 'SO2153233', 'SO2216957', 'SO2259783', 'SO2345829', 'SO2137316', 'SO2219376', 'SO2227896', 'SO2305329', 'SO2386207', 'SO2144163', 'SO2150300', 'SO2225464', 'SO2270175', 'SO2401653', 'SO2431210', 'SO2132719', 'SO2134773', 'SO2172071', 'SO2237166', 'SO2268733', 'SO2265221', 'SO2312706', 'SO2335799', 'SO2155837', 'SO2267488', 'SO2325500', 'SO2332662', 'SO2381004', 'SO2379608', 'SO2450347', 'SO2173129', 'SO2194275', 'SO2218532', 'SO2093606', 'SO2131972', 'SO2178212', 'SO2170142', 'SO2092572', 'SO2247610', 'SO2288973', 'SO2450191', 'SO2260443', 'SO2147886', 'SO2191351', 'SO2229630', 'SO2147070', 'SO2144796', 'SO2179954', 'SO2193605', 'SO2213675', 'SO2330186', 'SO2344551', 'SO2391351', 'SO2117842', 'SO2171593', 'SO2268166', 'SO2394354', 'SO2367270', 'SO2435752', 'SO2153250', 'SO2165410', 'SO2226483', 'SO2254439', 'SO2286898', 'SO2313917', 'SO2273325', 'SO2356532', 'SO2440336', 'SO2452287', 'SO2110893', 'SO2224203', 'SO2397366', 'SO2108558', 'SO2148154', 'SO2144765', 'SO2145054', 'SO2173399', 'SO2166836', 'SO2234788', 'SO2287419', 'SO2329141', 'SO2453643', 'SO2120430', 'SO2171049', 'SO2230024', 'SO2297776', 'SO2356069', 'SO2370570', 'SO2384643', 'SO2431358', 'SO2419387', 'SO2145290', 'SO2154132', 'SO2116164', 'SO2239745', 'SO2268569', 'SO2345064', 'SO2388394', 'SO2385245', 'SO2456855', 'SO2451086', 'SO2217325', 'SO2416507', 'SO2402248', 'SO2449253', 'SO2138795', 'SO2154205', 'SO2139882', 'SO2191074', 'SO2337383', 'SO2428275', 'SO2449284', 'SO2143505', 'SO2160991', 'SO2348466', 'SO2456268', 'SO2107536', 'SO2156446', 'SO2202065', 'SO2381601', 'SO2393225', 'SO2149216', 'SO2252119', 'SO2287158', 'SO2353229', 'SO2169957', 'SO2216966', 'SO2268445', 'SO2279725', 'SO2285406', 'SO2319105', 'SO2327781', 'SO2349006', 'SO2380127', 'SO2114369', 'SO2138814', 'SO2199435', 'SO2228476', 'SO2230431', 'SO2365001', 'SO2379617', 'SO2157898', 'SO2273734', 'SO2288041', 'SO2349882', 'SO2367218', 'SO2365005', 'SO2366920', 'SO2340120', 'SO2140859', 'SO2191922', 'SO2216108', 'SO2250550', 'SO2389494', 'SO2384448', 'SO2451987', 'SO2104368', 'SO2154692', 'SO2234310', 'SO2257895', 'SO2276523', 'SO2152047', 'SO2138800', 'SO2195557', 'SO2259745', 'SO2262473', 'SO2174856', 'SO2224629', 'SO2271608', 'SO2311526', 'SO2368410', 'SO2347425', 'SO2123046', 'SO2172062', 'SO2241820', 'SO2248912', 'SO2246690', 'SO2265286', 'SO2294316', 'SO2355172', 'SO2355091', 'SO2367707', 'SO2418088', 'SO2441246', 'SO2095308', 'SO2163939', 'SO2221235', 'SO2261284', 'SO2269474', 'SO2324991', 'SO2340968', 'SO2418532', 'SO2193690', 'SO2199385', 'SO2213059', 'SO2267868', 'SO2309908', 'SO2299035', 'SO2390347', 'SO2120469', 'SO2147509', 'SO2173967', 'SO2196525', 'SO2214608', 'SO2266453', 'SO2304925', 'SO2309559', 'SO2111957', 'SO2228610', 'SO2240478', 'SO2323304', 'SO2320307', 'SO2273199', 'SO2446950', 'SO2103205', 'SO2108873', 'SO2165942', 'SO2193731', 'SO2216668', 'SO2340771', 'SO2382905', 'SO2136985', 'SO2263107', 'SO2251235', 'SO2285425', 'SO2441943', 'SO2118664', 'SO2199384', 'SO2288894', 'SO2366403', 'SO2422286', 'SO2436210', 'SO2098249', 'SO2197777', 'SO2215458', 'SO2258544', 'SO2373579', 'SO2384718', 'SO2415404', 'SO2418070', 'SO2160359', 'SO2224025', 'SO2261598', 'SO2382884', 'SO2405379', 'SO2405288', 'SO2450959', 'SO2170033', 'SO2219366', 'SO2233609', 'SO2370869', 'SO2093328', 'SO2188898', 'SO2256834', 'SO2266398', 'SO2273406', 'SO2331971', 'SO2353835', 'SO2417833', 'SO2446460', 'SO2149896', 'SO2190544', 'SO2307651', 'SO2378799', 'SO2109845', 'SO2152148', 'SO2088616', 'SO2262599', 'SO2260790', 'SO2396465', 'SO2425996', 'SO2174303', 'SO2319624', 'SO2097228', 'SO2138528', 'SO2195021', 'SO2225876', 'SO2242278', 'SO2394227', 'SO2426098', 'SO2448915', 'SO2146903', 'SO2128893', 'SO2204568', 'SO2265415', 'SO2272400', 'SO2271656', 'SO2271659', 'SO2225009', 'SO2247671', 'SO2259913', 'SO2335263', 'SO2409183', 'SO2150170', 'SO2180890', 'SO2392995', 'SO2423803', 'SO2150747', 'SO2138597', 'SO2188174', 'SO2211369', 'SO2259674', 'SO2331408', 'SO2426594', 'SO2453963', 'SO2094482', 'SO2152720', 'SO2219743', 'SO2224529', 'SO2260379', 'SO2234818', 'SO2251746', 'SO2378937', 'SO2419752', 'SO2228595', 'SO2263221', 'SO2276065', 'SO2306458', 'SO2414290', 'SO2405077', 'SO2457653', 'SO2127377', 'SO2165296', 'SO2195332', 'SO2305205', 'SO2331439', 'SO2353437', 'SO2392567', 'SO2407590', 'SO2447924', 'SO2302946', 'SO2423775', 'SO2142700', 'SO2157232', 'SO2201017', 'SO2231928', 'SO2313018', 'SO2340350', 'SO2213800', 'SO2277694', 'SO2349154', 'SO2408134', 'SO2423624', 'SO2456642', 'SO2405801', 'SO2101944', 'SO2252960', 'SO2438059', 'SO2112376', 'SO2148633', 'SO2225101', 'SO2350051', 'SO2354010', 'SO2443838', 'SO2457493', 'SO2095156', 'SO2118551', 'SO2137076', 'SO2175769', 'SO2211888', 'SO2240672', 'SO2247277', 'SO2331974', 'SO2378655', 'SO2445963', 'SO2214361', 'SO2331539', 'SO2246934', 'SO2309618', 'SO2311733', 'SO2291787', 'SO2353805', 'SO2437918', 'SO2420349', 'SO2219756', 'SO2382336', 'SO2408794', 'SO2410177', 'SO2166051', 'SO2279016', 'SO2287033', 'SO2305871', 'SO2347878', 'SO2343149', 'SO2360551', 'SO2457619', 'SO2145671', 'SO2156777', 'SO2153258', 'SO2257799', 'SO2257436', 'SO2236968', 'SO2408236', 'SO2157811', 'SO2260733', 'SO2293785', 'SO2327327', 'SO2360816', 'SO2374010', 'SO2451701', 'SO2415702', 'SO2466225', 'SO2465944', 'SO2465685', 'SO2463744', 'SO2463531', 'SO2463275', 'SO2463252', 'SO2462136', 'SO2461653', 'SO2461562', 'SO2461496', 'SO2461385', 'SO2461200', 'SO2461144', 'SO2460729', 'SO2460165', 'SO2514883', 'SO2514393', 'SO2488098', 'SO2487544', 'SO2511194', 'SO2509475', 'SO2485174', 'SO2480668', 'SO2479831', 'SO2479803', 'SO2507748', 'SO2477547', 'SO2476074', 'SO2474818', 'SO2474112', 'SO2471420', 'SO2504280', 'SO2504269', 'SO2485268', 'SO2502853', 'SO2502493', 'SO2502101', 'SO2501349', 'SO2498233', 'SO2478725', 'SO2478701', 'SO2478630', 'SO2472836', 'SO2498977', 'SO2498514', 'SO2495909', 'SO2495722', 'SO2487969', 'SO2495056', 'SO2494836', 'SO2492633', 'SO2493104', 'SO2492673', 'SO2491255', 'SO2489491', 'SO2489144', 'SO2486921', 'SO2484166', 'SO2490313', 'SO2482139', 'SO2481938', 'SO2481674', 'SO2481638', 'SO2472673', 'SO2476890', 'SO2476880', 'SO2475359', 'SO2473843', 'SO2458141', 'SO2458086', 'SO2447002', 'SO2429723', 'SO2485795', 'SO2507239', 'SO2468304', 'SO2505167', 'SO2481090')""")
    invoice_records = mycursor.fetchall()
    #Lista de SO a las que se les creó una credit_notes
    so_modified = []
    #Lista de las facturas enlazadas a la SO y no existen
    inv_no_exist = []
    #Lista de SO que ya contaban con credit_notes antes del script
    so_with_refund = []
    #Lista de nombres de las notas de crédito creadas
    nc_created = []
    #Lista de SO que no existen en la factura global que tienen enlazada
    so_no_exist_in_invoice = []
    #Lista de facturas origen
    so_origin_invoice = []
    #Lista de referencias MKP para cada SO
    so_mkp_reference = []
    # Lista de total de la NC
    nc_amount_total = []
    print('----------------------------------------------------------------')
    print('Creando notas de crédito')
    print('Este proceso tomará unos minutos')
    #Creación de notas de crédito
    try:
        progress_bar = tqdm(total=len(invoice_records), desc="Procesando")
        for each in invoice_records:
            inv_origin_name = each[0] # Almacena el nombre de la SO
            inv_id = each[1] # Almacena el ID de la factura
            inv_name = each[2] # Almacena el nombre de la factura
            #Busca la factura que contenga el nombre de la SO
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', inv_id]]])
            if invoice:
                for inv in invoice:
                    inv_usage = 'G02'  # Uso del CFDI
                    inv_uuid = inv['l10n_mx_edi_cfdi_uuid']  # Folio fiscal de la factura
                    inv_uuid_origin = f'01|{inv_uuid}'
                    inv_journal_id = inv['journal_id'][0]
                    inv_payment = inv['l10n_mx_edi_payment_method_id'][0]
                    if inv_origin_name in inv['invoice_origin']:
                        #--------------------------AGREGAR CONDICIONAL PARA SABER SI TIENE NOTA DE CREDITO--------------------------
                        #Validamos si la SO ya tiene una nota de crédito creada
                        existing_credit_note = models.execute_kw(db_name, uid, password, 'account.move', 'search', [[['invoice_origin', '=', inv_origin_name], ['move_type', '=', 'out_refund']]])
                        if not existing_credit_note:
                            try:
                                #Busca la órden de venta
                                sale_order = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[['name', '=', inv_origin_name]]])[0]
                                # Obtiene los datos necesarios directo de la SO
                                sale_id = sale_order['id']
                                sale_name = sale_order['name']
                                sale_ref = sale_order['channel_order_reference']
                                sale_team = sale_order['team_id'][0]
                                #Busca el order line correspondiente de la orden de venta
                                sale_line_id = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[['order_id', '=', sale_id]]])
                                #Define los valores de la nota de crédito
                                inv_int = int(inv_id)
                                sale_int = int(sale_id)
                                refund_vals = {
                                    'ref': f'Reversión de: {inv_name}',
                                    'journal_id': inv_journal_id,
                                    'team_id': sale_team,
                                    'invoice_origin': sale_name,
                                    'payment_reference': inv_name,
                                    'invoice_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                                    # Puedes ajustar la fecha según tus necesidades
                                    'partner_id': inv['partner_id'][0],
                                    'l10n_mx_edi_usage': inv_usage,
                                    'l10n_mx_edi_origin': inv_uuid_origin,
                                    'l10n_mx_edi_payment_method_id': inv_payment,
                                    'reversed_entry_id': inv_int,
                                    'move_type': 'out_refund',  # Este campo indica que es una nota de crédito
                                    'invoice_line_ids': []
                                }
                                for lines in sale_line_id:
                                    nc_lines = {'product_id': lines['product_id'][0],
                                                'quantity': lines['product_uom_qty'],
                                                'name': lines['name'],  # Puedes ajustar esto según tus necesidades
                                                'price_unit': lines['price_unit'],
                                                'product_uom_id': lines['product_uom'][0],
                                                'tax_ids': [(6, 0, [lines['tax_id'][0]])],
                                                }
                                    refund_vals['invoice_line_ids'].append((0, 0, nc_lines))
                                #Crea la nota de crédito
                                create_nc = models.execute_kw(db_name, uid, password, 'account.move', 'create', [refund_vals])
                                #Actualiza la nota de crédito
                                #Agrega mensaje al Attachment de la nota de crédito
                                message = {
                                    'body': f"Esta nota de crédito fue creada a partir de la factura: {inv_name}, de la órden {sale_name}, con folio fiscal {inv_uuid}, a solicitud del equipo de Contabilidad, por el equipo de Tech mediante API.",
                                    'message_type': 'comment',
                                }
                                write_msg_nc = models.execute_kw(db_name, uid, password, 'account.move', 'message_post',[create_nc], message)
                                #Enlazamos la venta con la nueva factura
                                upd_sale = models.execute_kw(db_name, uid, password, 'sale.order', 'write', [[sale_id], {'invoice_ids': [(4, 0, create_nc)]}])
                                #Publicamos la nota de crédito
                                #upd_nc_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post', [create_nc])
                                #Timbramos la nota de crédito
                                #upd_nc_stamp = models.execute_kw(db_name, uid, password, 'account.move', 'button_process_edi_web_services',[create_nc])
                                #Buscamos el nombre de la factura ya creada
                                search_nc_name = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',[[['id', '=', create_nc]]])
                                nc_name = search_nc_name[0]['name']
                                nc_total = search_nc_name[0]['amount_total']
                                #Agregamos a las listas
                                so_modified.append(sale_name)
                                nc_created.append(nc_name)
                                nc_amount_total.append(nc_total)
                                so_origin_invoice.append(inv_name)
                                so_mkp_reference.append(sale_ref)
                                progress_bar.update(1)
                            except Exception as b:
                                print(f"En el armado de la factura y la creación: {b}")
                        else:
                            print(f"La órden {inv_origin_name} ya tiene una nota de crédito creada")
                            so_with_refund.append(inv_origin_name)
                            progress_bar.update(1)
                            continue
                    else:
                        print(f"La órden {inv_origin_name} no se encontró en la factura global")
                        so_no_exist_in_invoice.append(inv_origin_name)
                        progress_bar.update(1)
                        continue
            else:
                print(f"No hay una factura en la SO {inv_origin_name} por la cual se pueda crear una nota de crédito")
                inv_no_exist.append(inv_origin_name)
                progress_bar.update(1)
                continue
    except Exception as e:
       print(f"Error: no se pudo crear la nota de crédito: {e}")
    # Define el cuerpo del correo
    print('----------------------------------------------------------------')
    print('Creando correo y excel')
    #Excel
    try:
        # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'so_modified'
        sheet['B1'] = 'so_mkp_reference'
        sheet['C1'] = 'nc_created'
        sheet['D1'] = 'nc_amount_total'
        sheet['E1'] = 'so_origin_invoice'
        sheet['F1'] = 'inv_no_exist'
        sheet['G1'] = 'so_with_refund'
        sheet['H1'] = 'so_no_exist_in_invoice'

        # Agregar los resultados de los arrays
        for i in range(len(so_modified)):
            sheet['A{}'.format(i + 2)] = so_modified[i]
        for i in range(len(so_mkp_reference)):
            sheet['B{}'.format(i + 2)] = so_mkp_reference[i]
        for i in range(len(nc_created)):
            sheet['C{}'.format(i + 2)] = nc_created[i]
        for i in range(len(nc_amount_total)):
            sheet['D{}'.format(i + 2)] = nc_amount_total[i]
        for i in range(len(so_origin_invoice)):
            sheet['E{}'.format(i + 2)] = so_origin_invoice[i]
        for i in range(len(inv_no_exist)):
            sheet['F{}'.format(i + 2)] = inv_no_exist[i]
        for i in range(len(so_with_refund)):
            sheet['G{}'.format(i + 2)] = so_with_refund[i]
        for i in range(len(so_no_exist_in_invoice)):
            sheet['H{}'.format(i + 2)] = so_no_exist_in_invoice[i]

        # Guardar el archivo Excel en disco
        excel_file = 'notas_credito_globales_meli_' + today_date.strftime("%Y%m%d") + '.xlsx'
        workbook.save(excel_file)

        # Leer el contenido del archivo Excel
        with open(excel_file, 'rb') as file:
            file_data = file.read()
        file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    except Exception as a:
        print(f"Error: no se pudo crear el archivo de excel: {a}")
    # Correo
    try:
        msg = MIMEMultipart()
        body = '''\
                <html>
                  <head></head>
                  <body>
                    <p>Buenas</p>
                    <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script de notas de crédito.</p>
                    <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes a las cuales 
                    se les creó una nota de crédito, órdenes que no se les pudo crear una credit_notes, nombre de las notas de crédito 
                    creadas, órdenes que ya contaban con una nota de crédito antes de correr el script y órdenes que tuvieron 
                    algún error, por ejemplo que no existieran dentro de la factura global o no tuvieran una factura creada por la cual se pueda emitir una nota de crédito.</p>
                    </br>
                    <p>Sin más por el momento quedo al pendiente para resolver cualquier duda o comentario.</p>
                    </br>
                    <p>Muchas gracias</p>
                    </br>
                    <p>Un abrazo</p>
                  </body>
                </html>
                '''
        # Define remitente y destinatario
        msg = MIMEMultipart()
        msg['From'] = 'Tech anibal@wonderbrands.co'
        msg['To'] = ', '.join(
            ['anibal@wonderbrands.co', 'rosalba@wonderbrands.co', 'natalia@wonderbrands.co',
             'greta@somos-reyes.com',
             'contabilidad@somos-reyes.com', 'alex@wonderbrands.co', 'will@wonderbrands.co'])
        msg['Subject'] = 'Script Automático MELI- Creación de notas de crédito para facturas globales'
        # Adjuntar el cuerpo del correo
        msg.attach(MIMEText(body, 'html'))
        # Adjuntar el archivo Excel al mensaje
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(file_data)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=excel_file)
        msg.attach(attachment)
        print("Enviando correo")
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.starttls()
        smtpObj.login(smtp_username, smtp_password)
        smtpObj.sendmail(smtp_username, msg['To'], msg.as_string())
    except Exception as i:
        print(f"Error: no se pudo enviar el correo: {i}")

    print('----------------------------------------------------------------')
    print('Proceso NC globales Meli completado')
    print('----------------------------------------------------------------')

    # Cierre de conexiones
    progress_bar.close()
    smtpObj.quit()
    mycursor.close()
    mydb.close()
def reverse_invoice_global_amazon():
    # Obtener credenciales
    odoo_keys = get_odoo_access()
    psql_keys = get_psql_access()
    email_keys = get_email_access()
    # odoo
    server_url = odoo_keys['odoourl']
    db_name = odoo_keys['odoodb']
    username = odoo_keys['odoouser']
    password = odoo_keys['odoopassword']
    # correo
    smtp_server = email_keys['smtp_server']
    smtp_port = email_keys['smtp_port']
    smtp_username = email_keys['smtp_username']
    smtp_password = email_keys['smtp_password']

    print('----------------------------------------------------------------')
    print('NOTAS DE CRÉDITO GLOBALES AMAZON')
    print('----------------------------------------------------------------')
    print('Conectando API Odoo')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
    uid = common.authenticate(db_name, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
    print('Conexión con Odoo establecida')
    print('----------------------------------------------------------------')
    print('Conectando a Mysql')
    # Connect to MySQL database
    mydb = mysql.connector.connect(
        host=psql_keys['dbhost'],
        user=psql_keys['dbuser'],
        password=psql_keys['dbpassword'],
        database=psql_keys['database']
    )
    mycursor = mydb.cursor()
    print('----------------------------------------------------------------')
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')

    mycursor.execute("""SELECT c.name,
                               b.id 'account_move_id',
                               b.name/*,
                               d.order_id,
                               b.amount_total 'total_factura',
                               b.amount_untaxed 'subtotal_factura',
                               d.refunded_amt,
                               refund_date,
                               b.invoice_partner_display_name 'cliente',
                               'GLOBAL' as type,
                               'AMAZON' as marketplace*/
                        FROM somos_reyes.odoo_new_account_move_aux b
                        LEFT JOIN odoo_new_sale_order c
                        ON SUBSTRING_INDEX(SUBSTRING_INDEX(invoice_ids, ']', 1), '[', -1) = b.id
                        LEFT JOIN (SELECT a.order_id, max(STR_TO_DATE(fecha, '%d/%m/%Y')) 'refund_date', SUM(total - tarifas_de_amazon) * (-1) 'refunded_amt'
                                   FROM somos_reyes.amazon_payments_refunds a
                                   WHERE (total - tarifas_de_amazon) * (-1) > 0 AND STR_TO_DATE(fecha, '%d/%m/%Y') >= '2023-11-01' AND STR_TO_DATE(fecha, '%d/%m/%Y') <= '2023-11-30'
                                   GROUP BY 1) d
                        ON c.channel_order_id = d.order_id
                        LEFT JOIN (SELECT distinct invoice_origin FROM odoo_new_account_move_aux WHERE name like '%RINV%') e
                        ON c.name = e.invoice_origin
                        WHERE d.order_id is not null
                        AND e.invoice_origin is null
                        AND invoice_partner_display_name = 'PÚBLICO EN GENERAL'
                        AND (d.refunded_amt - b.amount_total > 1 OR d.refunded_amt - b.amount_total < -1)
                        AND d.refunded_amt - c.amount_total < 1 AND d.refunded_amt - c.amount_total > -1;""")
    invoice_records = mycursor.fetchall()
    #Lista de SO a las que se les creó una credit_notes
    so_modified = []
    #Lista de las facturas enlazadas a la SO y no existen
    inv_no_exist = []
    #Lista de SO que ya contaban con credit_notes antes del script
    so_with_refund = []
    #Lista de nombres de las notas de crédito creadas
    nc_created = []
    #Lista de SO que no existen en la factura global que tienen enlazada
    so_no_exist_in_invoice = []
    #Lista de facturas origen
    so_origin_invoice = []
    #Lista de referencias MKP para cada SO
    so_mkp_reference = []
    # Lista de total de la NC
    nc_amount_total = []
    print('----------------------------------------------------------------')
    print('Creando notas de crédito')
    print('Este proceso tomará unos minutos')
    #Creación de notas de crédito
    try:
        progress_bar = tqdm(total=len(invoice_records), desc="Procesando")
        for each in invoice_records:
            inv_origin_name = each[0] # Almacena el nombre de la SO
            inv_id = each[1] # Almacena el ID de la factura
            inv_name = each[2] # Almacena el nombre de la factura
            #Busca la factura que contenga el nombre de la SO
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', inv_id]]])
            if invoice:
                for inv in invoice:
                    inv_uuid = inv['l10n_mx_edi_cfdi_uuid']  # Folio fiscal de la factura
                    inv_usage = inv['l10n_mx_edi_usage']  # Folio fiscal de la factura
                    inv_journal_id = inv['journal_id'][0]
                    if inv_origin_name in inv['invoice_origin']:
                        #--------------------------AGREGAR CONDICIONAL PARA SABER SI TIENE NOTA DE CREDITO--------------------------
                        #Validamos si la SO ya tiene una nota de crédito creada
                        existing_credit_note = models.execute_kw(db_name, uid, password, 'account.move', 'search', [[['invoice_origin', '=', inv_origin_name], ['move_type', '=', 'out_refund']]])
                        if not existing_credit_note:
                            #Busca la órden de venta
                            sale_order = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[['name', '=', inv_origin_name]]])[0]
                            # Obtiene los datos necesarios directo de la SO
                            sale_id = sale_order['id']
                            sale_name = sale_order['name']
                            sale_ref = sale_order['channel_order_reference']
                            #Busca el order line correspondiente de la orden de venta
                            sale_line_id = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[['order_id', '=', sale_id]]])
                            #Define los valores de la nota de crédito
                            inv_int = int(inv_id)
                            sale_int = int(sale_id)
                            refund_vals = {
                                'ref': f'Reversión de: {inv_name}',
                                'journal_id': inv_journal_id,
                                'invoice_origin': sale_name,
                                'payment_reference': inv_name,
                                'invoice_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                                # Puedes ajustar la fecha según tus necesidades
                                'partner_id': inv['partner_id'][0],
                                'l10n_mx_edi_usage': inv_usage,
                                'reversed_entry_id': inv_int,
                                'move_type': 'out_refund',  # Este campo indica que es una nota de crédito
                                'invoice_line_ids': []
                            }
                            for lines in sale_line_id:
                                nc_lines = {'product_id': lines['product_id'][0],
                                            'quantity': lines['product_uom_qty'],
                                            'name': lines['name'],  # Puedes ajustar esto según tus necesidades
                                            'price_unit': lines['price_unit'],
                                            'product_uom_id': lines['product_uom'][0],
                                            'tax_ids': [(6, 0, [lines['tax_id'][0]])],
                                            }
                                refund_vals['invoice_line_ids'].append((0, 0, nc_lines))
                            #Crea la nota de crédito
                            create_nc = models.execute_kw(db_name, uid, password, 'account.move', 'create', [refund_vals])
                            #Actualiza la nota de crédito
                            #Agrega mensaje al Attachment de la nota de crédito
                            message = {
                                'body': f"Esta nota de crédito fue creada a partir de la factura: {inv_name}, de la órden {sale_name}, con folio fiscal {inv_uuid}, a solicitud del equipo de Contabilidad, por el equipo de Tech mediante API.",
                                'message_type': 'comment',
                            }
                            write_msg_nc = models.execute_kw(db_name, uid, password, 'account.move', 'message_post',[create_nc], message)
                            #Enlazamos la venta con la nueva factura
                            upd_sale = models.execute_kw(db_name, uid, password, 'sale.order', 'write', [[sale_id], {'invoice_ids': [(4, 0, create_nc)]}])
                            #Publicamos la nota de crédito
                            #upd_nc_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post', [create_nc])
                            #Timbramos la nota de crédito
                            #upd_nc_stamp = models.execute_kw(db_name, uid, password, 'account.move', 'button_process_edi_web_services',[create_nc])
                            #Buscamos el nombre de la factura ya creada
                            search_nc_name = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',[[['id', '=', create_nc]]])
                            nc_name = search_nc_name[0]['name']
                            nc_total = search_nc_name[0]['amount_total']
                            #Agregamos a las listas
                            so_modified.append(sale_name)
                            nc_created.append(nc_name)
                            nc_amount_total.append(nc_total)
                            so_origin_invoice.append(inv_name)
                            so_mkp_reference.append(sale_ref)
                            progress_bar.update(1)
                        else:
                            print(f"La órden {inv_origin_name} ya tiene una nota de crédito creada")
                            so_with_refund.append(inv_origin_name)
                            progress_bar.update(1)
                            continue
                    else:
                        print(f"La órden {inv_origin_name} no se encontró en la factura global")
                        so_no_exist_in_invoice.append(inv_origin_name)
                        progress_bar.update(1)
                        continue
            else:
                print(f"No hay una factura en la SO {inv_origin_name} por la cual se pueda crear una nota de crédito")
                inv_no_exist.append(inv_origin_name)
                progress_bar.update(1)
                continue
    except Exception as e:
       print(f"Error: no se pudo crear la nota de crédito: {e}")
    # Define el cuerpo del correo
    print('----------------------------------------------------------------')
    print('Creando correo y excel')
    #Excel
    try:
        # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'so_modified'
        sheet['B1'] = 'so_mkp_reference'
        sheet['C1'] = 'nc_created'
        sheet['D1'] = 'nc_amount_total'
        sheet['E1'] = 'so_origin_invoice'
        sheet['F1'] = 'inv_no_exist'
        sheet['G1'] = 'so_with_refund'
        sheet['H1'] = 'so_no_exist_in_invoice'

        # Agregar los resultados de los arrays
        for i in range(len(so_modified)):
            sheet['A{}'.format(i + 2)] = so_modified[i]
        for i in range(len(so_mkp_reference)):
            sheet['B{}'.format(i + 2)] = so_mkp_reference[i]
        for i in range(len(nc_created)):
            sheet['C{}'.format(i + 2)] = nc_created[i]
        for i in range(len(nc_amount_total)):
            sheet['D{}'.format(i + 2)] = nc_amount_total[i]
        for i in range(len(so_origin_invoice)):
            sheet['E{}'.format(i + 2)] = so_origin_invoice[i]
        for i in range(len(inv_no_exist)):
            sheet['F{}'.format(i + 2)] = inv_no_exist[i]
        for i in range(len(so_with_refund)):
            sheet['G{}'.format(i + 2)] = so_with_refund[i]
        for i in range(len(so_no_exist_in_invoice)):
            sheet['H{}'.format(i + 2)] = so_no_exist_in_invoice[i]

        # Guardar el archivo Excel en disco
        excel_file = 'notas_credito_globales_amazon_' + today_date.strftime("%Y%m%d") + '.xlsx'
        workbook.save(excel_file)

        # Leer el contenido del archivo Excel
        with open(excel_file, 'rb') as file:
            file_data = file.read()
        file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    except Exception as a:
        print(f"Error: no se pudo crear el archivo de excel: {a}")
    # Correo
    try:
        msg = MIMEMultipart()
        body = '''\
                <html>
                  <head></head>
                  <body>
                    <p>Buenas</p>
                    <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script de notas de crédito.</p>
                    <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes a las cuales 
                    se les creó una nota de crédito, órdenes que no se les pudo crear una credit_notes, nombre de las notas de crédito 
                    creadas, órdenes que ya contaban con una nota de crédito antes de correr el script y órdenes que tuvieron 
                    algún error, por ejemplo que no existieran dentro de la factura global o no tuvieran una factura creada por la cual se pueda emitir una nota de crédito.</p>
                    </br>
                    <p>Sin más por el momento quedo al pendiente para resolver cualquier duda o comentario.</p>
                    </br>
                    <p>Muchas gracias</p>
                    </br>
                    <p>Un abrazo</p>
                  </body>
                </html>
                '''
        # Define remitente y destinatario
        msg = MIMEMultipart()
        msg['From'] = 'Tech anibal@wonderbrands.co'
        msg['To'] = ', '.join(
            ['anibal@wonderbrands.co', 'rosalba@wonderbrands.co', 'natalia@wonderbrands.co',
             'greta@somos-reyes.com',
             'contabilidad@somos-reyes.com', 'alex@wonderbrands.co', 'will@wonderbrands.co'])
        msg['Subject'] = 'Script Automático Amazon - Creación de notas de crédito para facturas globales'
        # Adjuntar el cuerpo del correo
        msg.attach(MIMEText(body, 'html'))
        # Adjuntar el archivo Excel al mensaje
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(file_data)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=excel_file)
        msg.attach(attachment)
        print("Enviando correo")
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.starttls()
        smtpObj.login(smtp_username, smtp_password)
        smtpObj.sendmail(smtp_username, msg['To'], msg.as_string())
    except Exception as i:
        print(f"Error: no se pudo enviar el correo: {i}")

    print('----------------------------------------------------------------')
    print('Proceso NC Amazon completado')
    print('----------------------------------------------------------------')

    # Cierre de conexiones
    progress_bar.close()
    smtpObj.quit()
    mycursor.close()
    mydb.close()

if __name__ == "__main__":
    reverse_invoice_global_meli()
    reverse_invoice_global_amazon()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duraciòn del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')