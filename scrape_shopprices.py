from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup
import requests
from datetime import datetime, date
import json

with open('productDict.json', 'r') as inFile:
    productDict = json.load(inFile)


def getKeyValue(element):
    key = element.get('data-name')
    value = element.get('data-id')

    return key, value


def getProductDict():
    r = requests.get('https://sellup.com.sg/sell/apple-iphone.html')
    soup = BeautifulSoup(r.content, 'html.parser')
    evalPageLinks_arr = soup.select('a[href*="/sell/Apple"]')
    productPageLinks = []
    for listing in evalPageLinks_arr:
        link = listing.get("href")
        if link not in productPageLinks:
            productPageLinks.append(link)

    print(f'{len(productPageLinks)} products found')

    firstRun = True

    productDict = {
      "products": []
    }

    for productLink in productPageLinks:
        r = requests.get('https://sellup.com.sg' + productLink)
        soup = BeautifulSoup(r.content, 'html.parser')
        if firstRun: #Get Option categories and save into array for first run
            data_specs_arr = []
            data_selectors = soup.select('li[class*="option"]')
            for x in data_selectors:
                spec_name = x.get('data-specsname')
                if spec_name not in data_specs_arr:
                    data_specs_arr.append(spec_name)
            firstRun = False

        product_name = soup.select_one('input[id="product_name"]').get('value')
        device_specid = soup.select_one('li[data-devicespecsid*="deviceSpecsId"]').get('data-devicespecsid')
        device_reqid = soup.select_one('input[name="goods_id"]').get('value')

        elements = {"storage": soup.select('li[data-specsname="Built-In Storage"]'),
                    "colour": soup.select('li[data-specsname="Colour"]'),
                    "cop": soup.select('li[data-specsname="Country of Purchase"]'),
                    "batt_health": soup.select('li[data-specsname="Battery Health"]'),
                    "housing": soup.select('li[data-specsname="Housing / Casing"]'),
                    "screen": soup.select('li[data-specsname="Front Glass Panel (Screen)"]'),
                    "accessories": soup.select('li[data-specsname="Accessories"]')}

        current = {
            "deviceSpecId": device_specid,
            "deviceReqId": device_reqid,
            "name": product_name,
            "storage": {},
            "colour": {},
            "cop": {},
            "batt_health": {},
            "housing":{},
            "screen":{},
            "accessories":{}
        }

        for type, cat_elements in elements.items():
            for element in cat_elements:
                key, value = getKeyValue(element)
                current[type][key] = value

        productDict["products"].append(current)

    return productDict


def updateProductDict(fileName):
    productDict = getProductDict()
    with open(fileName, 'w') as outFile:
        outFile.write(str(productDict).replace("'", '"'))

    return True


def getSellUpPrices(goods_id, storage, colour, cop, housing, screen, batt, accessory):
    if accessory:
        data = f'action=Calculate&deviceType=1&data[]={storage}&data[]={colour}&data[]={cop}&data[]={housing}&data[]={screen}&data[]={batt}&data[]={accessory[0]}&data[]={accessory[1]}&goods_id={goods_id}'
    else:
        data = f'action=Calculate&deviceType=1&data[]={storage}&data[]={colour}&data[]={cop}&data[]={housing}&data[]={screen}&data[]={batt}&goods_id={goods_id}'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15',
        'X-Requested-With': 'XMLHttpRequest',
    }
    r = requests.post('https://sellup.com.sg/ajax.php', data=data, headers=headers)

    token = r.json()['data']['token']

    data = f'action=walkIn&token={token}&serviceAreaIds[]=&selectedDate={str(date.today())}&timeslot=&latitude=0&longitude=0'
    r = requests.post('https://sellup.com.sg/ajax.php', data=data, headers=headers)

    max = r.json()['data']['dealerPrices'][0]['totalPrice']

    #
    # max = 0
    # for q in r.json()["data"]["dealerPrices"]:
    #     if q["totalPrice"] > max:
    #         max = q["totalPrice"]

    return max

filename = datetime.now().strftime("%d %b %I%M %p")
with open(f'{filename} - Price Matrix.csv', 'w') as inFile:
    inFile.write('')


def getSearchID(phoneName, attribute, value):
    with open('productDict.json', 'r') as inFile:
        productDict = json.load(inFile)

    try:
        for product in productDict["products"]:
            if str(product["name"]).lower() == str(phoneName).lower():
                searchID = product[attribute][value]
                return searchID
    except Exception as e:
        return e


def getPhoneReqID(phoneName):
    with open('productDict.json', 'r') as inFile:
        productDict = json.load(inFile)

    try:
        for product in productDict["products"]:
            if str(product["name"]).lower() == str(phoneName).lower():
                reqID = product["deviceReqId"]
                return reqID
    except Exception as e:
        return e


def getProductIDs(phoneName):
    with open('productDict.json', 'r') as inFile:
        productDict = json.load(inFile)

    try:
        for product in productDict["products"]:
            if str(product["name"]).lower() == str(phoneName).lower():
                return product
    except Exception as e:
        return e


def getShopPrice_simpleInfo(phoneName, storage, battHealth):

    productDict = getProductIDs(phoneName)
    reqID = productDict['deviceReqId']
    storageID = productDict['storage'][storage]
    colourID = list(productDict['colour'].values())[0]
    copID = list(productDict['cop'].values())[0]

    if int(battHealth) >= 91:
        battHealthID = productDict['batt_health']['91% & Above']
    elif int(battHealth) >= 86:
        battHealthID = productDict['batt_health']['86% - 90%']
    else:
        battHealthID = productDict['batt_health']['85% & Below']
    housingID_A = list(productDict['housing'].values())[0]
    screenID_A = list(productDict['screen'].values())[0]
    housingID_B = list(productDict['housing'].values())[1]
    # screenID_A = list(productDict['housing'].values())[1] #futureproof, can enable if needed i guess

    FAA = getSellUpPrices(reqID, storageID, colourID, copID, housingID_A, screenID_A, battHealthID, False) #FullSet, Grade A Housing & Screen
    FBA = getSellUpPrices(reqID, storageID, colourID, copID, housingID_B, screenID_A, battHealthID, False) #FullSet, Grade B Housing & Grade A Screen

    return {"FAA": FAA, "FBA": FBA}
#
# productDict = {"products": [{"deviceSpecId": "deviceSpecsId_43007", "deviceReqId": "6466", "name": "iPhone 14", "storage": {"128GB": "100650", "256GB": "100651", "512GB": "100652"}, "colour": {"Blue": "100653", "Purple": "100654", "Midnight  ": "100655", "Starlight": "100656", "Red": "100657"}, "cop": {"Local Singapore Set": "100604", "Export Set": "100605"}, "batt_health": {"91% & Above": "100606", "86% - 90%": "100607", "85% & Below": "100608", "Battery Service": "100609"}, "housing": {"Grade A": "100596", "Grade B": "100597", "Grade C": "100598", "Defective": "100599"}, "screen": {"Grade A": "100600", "Grade B": "100601", "Grade C": "100602", "Defective": "100603"}, "accessories": {"Charging Cable": "100616", "Box": "100617"}}, {"deviceSpecId": "deviceSpecsId_43025", "deviceReqId": "6467", "name": "iPhone 14 Plus", "storage": {"128GB": "100712", "256GB": "100713", "512GB": "100714"}, "colour": {"Blue": "100715", "Purple": "100716", "Midnight  ": "100717", "Starlight": "100718", "Red": "100719"}, "cop": {"Local Singapore Set": "100666", "Export Set": "100667"}, "batt_health": {"91% & Above": "100668", "86% - 90%": "100669", "85% & Below": "100670", "Battery Service": "100671"}, "housing": {"Grade A": "100658", "Grade B": "100659", "Grade C": "100660", "Defective": "100661"}, "screen": {"Grade A": "100662", "Grade B": "100663", "Grade C": "100664", "Defective": "100665"}, "accessories": {"Charging Cable": "100678", "Box": "100679"}}, {"deviceSpecId": "deviceSpecsId_43044", "deviceReqId": "6468", "name": "iPhone 14 Pro", "storage": {"128GB": "100776", "256GB": "100777", "512GB": "100778", "1TB": "100779"}, "colour": {"Deep Purple": "100780", "Gold": "100781", "Silver": "100782", "Space Black": "100783"}, "cop": {"Local Singapore Set": "100728", "Export Set": "100729"}, "batt_health": {"91% & Above": "100730", "86% - 90%": "100731", "85% & Below": "100732", "Battery Service": "100733"}, "housing": {"Grade A": "100720", "Grade B": "100721", "Grade C": "100722", "Defective": "100723"}, "screen": {"Grade A": "100724", "Grade B": "100725", "Grade C": "100726", "Defective": "100727"}, "accessories": {"Charging Cable": "100740", "Box": "100741"}}, {"deviceSpecId": "deviceSpecsId_43062", "deviceReqId": "6469", "name": "iPhone 14 Pro Max", "storage": {"128GB": "100838", "256GB": "100839", "512GB": "100840", "1TB": "100841"}, "colour": {"Deep Purple": "100842", "Gold": "100843", "Silver": "100844", "Space Black": "100845"}, "cop": {"Local Singapore Set": "100792", "Export Set": "100793"}, "batt_health": {"91% & Above": "100794", "86% - 90%": "100795", "85% & Below": "100796", "Battery Service": "100797"}, "housing": {"Grade A": "100784", "Grade B": "100785", "Grade C": "100786", "Defective": "100787"}, "screen": {"Grade A": "100788", "Grade B": "100789", "Grade C": "100790", "Defective": "100791"}, "accessories": {"Charging Cable": "100804", "Box": "100805"}}, {"deviceSpecId": "deviceSpecsId_41417", "deviceReqId": "6357", "name": "iPhone SE 2022 (3rd Gen)", "storage": {"64GB": "95595", "128GB": "95596", "256GB": "95597"}, "colour": {"Midnight  ": "95598", "Starlight": "95599", "Red": "95600"}, "cop": {"Local Singapore Set": "95550", "Export Set": "95551"}, "batt_health": {"91% & Above": "95552", "86% - 90%": "95553", "85% & Below": "95554", "Battery Service": "95555"}, "housing": {"Grade A": "95542", "Grade B": "95543", "Grade C": "95544", "Defective": "95545"}, "screen": {"Grade A": "95546", "Grade B": "95547", "Grade C": "95548", "Defective": "95549"}, "accessories": {"Charging Cable": "95562", "Box": "95563"}}, {"deviceSpecId": "deviceSpecsId_37529", "deviceReqId": "6129", "name": "iPhone 13", "storage": {"128GB": "83670", "256GB": "83671", "512GB": "83672"}, "colour": {"Red": "83673", "Starlight": "83674", "Midnight  ": "83675", "Pink": "83676", "Blue": "83677", "Green": "95715"}, "cop": {"Local Singapore Set": "83631", "Export Set": "83632"}, "batt_health": {"91% & Above": "84769", "86% - 90%": "84770", "85% & Below": "84771", "Battery Service": "84772"}, "housing": {"Grade A": "83623", "Grade B": "83624", "Grade C": "83625", "Defective": "83626"}, "screen": {"Grade A": "83627", "Grade B": "83628", "Grade C": "83629", "Defective": "83630"}, "accessories": {"Charging Cable": "83640", "Box": "83641"}}, {"deviceSpecId": "deviceSpecsId_37546", "deviceReqId": "6130", "name": "iPhone 13 Pro", "storage": {"128GB": "83728", "256GB": "83729", "512GB": "83730", "1TB": "83731"}, "colour": {"Sierra Blue": "83732", "Gold": "83733", "Silver": "83734", "Graphite": "83735", "Alpine Green": "95540"}, "cop": {"Local Singapore Set": "83686", "Export Set": "83687"}, "batt_health": {"91% & Above": "84775", "86% - 90%": "84776", "85% & Below": "84777", "Battery Service": "84778"}, "housing": {"Grade A": "83678", "Grade B": "83679", "Grade C": "83680", "Defective": "83681"}, "screen": {"Grade A": "83682", "Grade B": "83683", "Grade C": "83684", "Defective": "83685"}, "accessories": {"Charging Cable": "83695", "Box": "83696"}}, {"deviceSpecId": "deviceSpecsId_37563", "deviceReqId": "6131", "name": "iPhone 13 Pro Max", "storage": {"128GB": "83786", "256GB": "83787", "512GB": "83788", "1TB": "83789"}, "colour": {"Gold": "83790", "Silver": "83791", "Sierra Blue": "83792", "Graphite": "83793", "Alpine Green": "95541"}, "cop": {"Local Singapore Set": "83744", "Export Set": "83745"}, "batt_health": {"91% & Above": "84781", "86% - 90%": "84782", "85% & Below": "84783", "Battery Service": "84784"}, "housing": {"Grade A": "83736", "Grade B": "83737", "Grade C": "83738", "Defective": "83739"}, "screen": {"Grade A": "83740", "Grade B": "83741", "Grade C": "83742", "Defective": "83743"}, "accessories": {"Charging Cable": "83753", "Box": "83754"}}, {"deviceSpecId": "deviceSpecsId_37512", "deviceReqId": "6128", "name": "iPhone 13 mini", "storage": {"128GB": "83615", "256GB": "83616", "512GB": "83617"}, "colour": {"Red": "83618", "Starlight": "83619", "Midnight  ": "83620", "Blue": "83621", "Pink": "83622", "Green": "95714"}, "cop": {"Local Singapore Set": "83573", "Export Set": "83574"}, "batt_health": {"91% & Above": "84763", "86% - 90%": "84764", "85% & Below": "84765", "Battery Service": "84766"}, "housing": {"Grade A": "83565", "Grade B": "83566", "Grade C": "83567", "Defective": "83568"}, "screen": {"Grade A": "83569", "Grade B": "83570", "Grade C": "83571", "Defective": "83572"}, "accessories": {"Charging Cable": "83582", "Box": "83583"}}, {"deviceSpecId": "deviceSpecsId_33908", "deviceReqId": "5999", "name": "iPhone 12", "storage": {"64GB": "70719", "128GB": "70720", "256GB": "70721"}, "colour": {"White": "70722", "Black": "70723", "Blue": "70724", "Green": "70725", "Red": "70726", "Purple": "81415"}, "cop": {"Local Singapore Set": "71440", "Export Set": "71441"}, "batt_health": {"91% & Above": "84745", "86% - 90%": "84746", "85% & Below": "84747", "Battery Service": "84748"}, "housing": {"Grade A": "70671", "Grade B": "70672", "Grade C": "70673", "Defective": "70674"}, "screen": {"Grade A": "70675", "Grade B": "70676", "Grade C": "70677", "Defective": "70678"}, "accessories": {"Charging Cable": "70684", "Box": "70685"}}, {"deviceSpecId": "deviceSpecsId_33890", "deviceReqId": "5998", "name": "iPhone 12 mini", "storage": {"64GB": "70663", "128GB": "70664", "256GB": "70665"}, "colour": {"White": "70666", "Black": "70667", "Blue": "70668", "Green": "70669", "Red": "70670", "Purple": "81414"}, "cop": {"Local Singapore Set": "71432", "Export Set": "71433"}, "batt_health": {"91% & Above": "84739", "86% - 90%": "84740", "85% & Below": "84741", "Battery Service": "84742"}, "housing": {"Grade A": "70615", "Grade B": "70616", "Grade C": "70617", "Defective": "70618"}, "screen": {"Grade A": "70619", "Grade B": "70620", "Grade C": "70621", "Defective": "70622"}, "accessories": {"Charging Cable": "70628", "Box": "70629"}}, {"deviceSpecId": "deviceSpecsId_33926", "deviceReqId": "6000", "name": "iPhone 12 Pro", "storage": {"128GB": "70775", "256GB": "70776", "512GB": "70777"}, "colour": {"Graphite": "70778", "Silver": "70779", "Gold": "70780", "Pacific Blue": "70781"}, "cop": {"Local Singapore Set": "71448", "Export Set": "71449"}, "batt_health": {"91% & Above": "84751", "86% - 90%": "84752", "85% & Below": "84753", "Battery Service": "84754"}, "housing": {"Grade A": "70727", "Grade B": "70728", "Grade C": "70729", "Defective": "70730"}, "screen": {"Grade A": "70731", "Grade B": "70732", "Grade C": "70733", "Defective": "70734"}, "accessories": {"Charging Cable": "70740", "Box": "70741"}}, {"deviceSpecId": "deviceSpecsId_33944", "deviceReqId": "6001", "name": "iPhone 12 Pro Max", "storage": {"128GB": "70830", "256GB": "70831", "512GB": "70832"}, "colour": {"Graphite": "70833", "Silver": "70834", "Gold": "70835", "Pacific Blue": "70836"}, "cop": {"Local Singapore Set": "71456", "Export Set": "71457"}, "batt_health": {"91% & Above": "84757", "86% - 90%": "84758", "85% & Below": "84759", "Battery Service": "84760"}, "housing": {"Grade A": "70782", "Grade B": "70783", "Grade C": "70784", "Defective": "70785"}, "screen": {"Grade A": "70786", "Grade B": "70787", "Grade C": "70788", "Defective": "70789"}, "accessories": {"Charging Cable": "70795", "Box": "70796"}}, {"deviceSpecId": "deviceSpecsId_21676", "deviceReqId": "5870", "name": "iPhone SE 2020 (2nd Gen)", "storage": {"64GB": "37904", "128GB": "37905", "256GB": "37906"}, "colour": {"Black": "37907", "White": "37908", "Red": "37909"}, "cop": {"Local Singapore Set": "40198", "Export Set": "40199"}, "batt_health": {"91% & Above": "84731", "86% - 90%": "84732", "85% & Below": "84733", "Battery Service": "84734"}, "housing": {"Grade A": "37877", "Grade B": "37878", "Grade C": "37879", "Defective": "37880"}, "screen": {"Grade A": "37881", "Grade B": "37882", "Grade C": "37883", "Defective": "37884"}, "accessories": {"Wall Charger": "37889", "Charging Cable": "37890", "Box": "37891", "Ear Phone": "37892"}}, {"deviceSpecId": "deviceSpecsId_20767", "deviceReqId": "5840", "name": "iPhone 11 Pro", "storage": {"64GB": "35864", "256GB": "35865", "512GB": "35866"}, "colour": {"Space Gray": "35867", "Silver": "35868", "Gold": "35869", "Midnight Green": "35870"}, "cop": {"Local Singapore Set": "37008", "Export Set": "37009"}, "batt_health": {"91% & Above": "84711", "86% - 90%": "84712", "85% & Below": "84713", "Battery Service": "84714"}, "housing": {"Grade A": "35770", "Grade B": "35771", "Grade C": "35772", "Defective": "35773"}, "screen": {"Grade A": "35774", "Grade B": "35775", "Grade C": "35776", "Defective": "35777"}, "accessories": {"Box": "36408", "Charging Cable": "36409", "Ear Phone": "36410", "Wall Charger": "36411"}}, {"deviceSpecId": "deviceSpecsId_20792", "deviceReqId": "5841", "name": "iPhone 11 Pro Max", "storage": {"64GB": "35908", "256GB": "35909", "512GB": "35910"}, "colour": {"Space Gray": "35911", "Silver": "35912", "Gold": "35913", "Midnight Green": "35914"}, "cop": {"Local Singapore Set": "37010", "Export Set": "37011"}, "batt_health": {"91% & Above": "84715", "86% - 90%": "84716", "85% & Below": "84717", "Battery Service": "84718"}, "housing": {"Grade A": "35784", "Grade B": "35785", "Grade C": "35786", "Defective": "35787"}, "screen": {"Grade A": "35788", "Grade B": "35789", "Grade C": "35790", "Defective": "35791"}, "accessories": {"Box": "36412", "Charging Cable": "36413", "Ear Phone": "36414", "Wall Charger": "36415"}}, {"deviceSpecId": "deviceSpecsId_20742", "deviceReqId": "5839", "name": "iPhone 11", "storage": {"64GB": "35816", "128GB": "35817", "256GB": "35818"}, "colour": {"Black": "35819", "Green": "35820", "Yellow": "35821", "Purple": "35822", "Red": "35823", "White": "35824"}, "cop": {"Local Singapore Set": "37006", "Export Set": "37007"}, "batt_health": {"91% & Above": "84707", "86% - 90%": "84708", "85% & Below": "84709", "Battery Service": "84710"}, "housing": {"Grade A": "35756", "Grade B": "35757", "Grade C": "35758", "Defective": "35759"}, "screen": {"Grade A": "35760", "Grade B": "35761", "Grade C": "35762", "Defective": "35763"}, "accessories": {"Box": "36404", "Charging Cable": "36405", "Wall Charger": "86038", "Ear Phone": "86039"}}, {"deviceSpecId": "deviceSpecsId_17099", "deviceReqId": "5746", "name": "iPhone XR", "storage": {"64GB": "27844", "128GB": "27845", "256GB": "27846"}, "colour": {"White": "27847", "Black": "27848", "Blue": "27849", "Yellow": "27850", "Coral": "27851", "Red": "27852"}, "cop": {"Local Singapore Set": "37004", "Export Set": "37005"}, "batt_health": {"91% & Above": "84703", "86% - 90%": "84704", "85% & Below": "84705", "Battery Service": "84706"}, "housing": {"Grade A": "27762", "Grade B": "27763", "Grade C": "27764", "Defective": "27765"}, "screen": {"Grade A": "27766", "Grade B": "27767", "Grade C": "27768", "Defective": "27769"}, "accessories": {"Box": "36400", "Charging Cable": "36401", "Ear Phone": "36402", "Wall Charger": "36403"}}, {"deviceSpecId": "deviceSpecsId_17061", "deviceReqId": "5744", "name": "iPhone XS", "storage": {"64GB": "27794", "256GB": "27795", "512GB": "27796"}, "colour": {"Silver": "27797", "Space Grey": "27798", "Gold": "27799"}, "cop": {"Local Singapore Set": "37000", "Export Set": "37001"}, "batt_health": {"91% & Above": "84695", "86% - 90%": "84696", "85% & Below": "84697", "Battery Service": "84698"}, "housing": {"Grade A": "27734", "Grade B": "27735", "Grade C": "27736", "Defective": "27737"}, "screen": {"Grade A": "27738", "Grade B": "27739", "Grade C": "27740", "Defective": "27741"}, "accessories": {"Box": "36392", "Charging Cable": "36393", "Ear Phone": "36394", "Wall Charger": "36395"}}, {"deviceSpecId": "deviceSpecsId_17080", "deviceReqId": "5745", "name": "iPhone XS Max", "storage": {"64GB": "27819", "256GB": "27820", "512GB": "27821"}, "colour": {"Space Grey": "27822", "Silver": "27823", "Gold": "27824"}, "cop": {"Local Singapore Set": "37002", "Export Set": "37003"}, "batt_health": {"91% & Above": "84699", "86% - 90%": "84700", "85% & Below": "84701", "Battery Service": "84702"}, "housing": {"Grade A": "27748", "Grade B": "27749", "Grade C": "27750", "Defective": "27751"}, "screen": {"Grade A": "27752", "Grade B": "27753", "Grade C": "27754", "Defective": "27755"}, "accessories": {"Box": "36396", "Charging Cable": "36397", "Ear Phone": "36398", "Wall Charger": "36399"}}, {"deviceSpecId": "deviceSpecsId_15370", "deviceReqId": "5671", "name": "iPhone X", "storage": {"64GB": "23136", "256GB": "23137"}, "colour": {"Space Gray": "23138", "Silver": "23139"}, "cop": {"Local Singapore Set": "36998", "Export Set": "36999"}, "batt_health": {"91% & Above": "84691", "86% - 90%": "84692", "85% & Below": "84693", "Battery Service": "84694"}, "housing": {"Grade A": "23059", "Grade B": "23060", "Grade C": "23061", "Defective": "26599"}, "screen": {"Grade A": "23062", "Grade B": "23063", "Grade C": "23064", "Defective": "27253"}, "accessories": {"Box": "36388", "Charging Cable": "36389", "Ear Phone": "36390", "Wall Charger": "36391"}}, {"deviceSpecId": "deviceSpecsId_15333", "deviceReqId": "5669", "name": "iPhone 8", "storage": {"64GB": "23089", "256GB": "23090"}, "colour": {"Silver": "23091", "Space Gray": "23092", "Gold": "23093", "Red": "25267"}, "cop": {"Local Singapore Set": "36994", "Export Set": "36995"}, "batt_health": {"91% & Above": "84683", "86% - 90%": "84684", "85% & Below": "84685", "Battery Service": "84686"}, "housing": {"Grade A": "23031", "Grade B": "23032", "Grade C": "23033", "Defective": "26597"}, "screen": {"Grade A": "23034", "Grade B": "23035", "Grade C": "23036", "Defective": "27251"}, "accessories": {"Box": "36380", "Charging Cable": "36381", "Ear Phone": "36382", "Wall Charger": "36383"}}, {"deviceSpecId": "deviceSpecsId_15352", "deviceReqId": "5670", "name": "iPhone 8 Plus", "storage": {"64GB": "23113", "256GB": "23114"}, "colour": {"Gold": "23115", "Silver": "23116", "Space Gray": "23117", "Red": "25268"}, "cop": {"Local Singapore Set": "36996", "Export Set": "36997"}, "batt_health": {"91% & Above": "84687", "86% - 90%": "84688", "85% & Below": "84689", "Battery Service": "84690"}, "housing": {"Grade A": "23045", "Grade B": "23046", "Grade C": "23047", "Defective": "26598"}, "screen": {"Grade A": "23048", "Grade B": "23049", "Grade C": "23050", "Defective": "27252"}, "accessories": {"Box": "36384", "Charging Cable": "36385", "Ear Phone": "36386", "Wall Charger": "36387"}}, {"deviceSpecId": "deviceSpecsId_8362", "deviceReqId": "5494", "name": "iPhone 7", "storage": {"32GB": "10281", "128GB": "10282", "256GB": "10283"}, "colour": {"Jet Black": "10284", "Black": "10285", "Silver": "10286", "Gold": "10287", "Rose Gold": "10288", "Red": "20954"}, "cop": {"Local Singapore Set": "36990", "Export Set": "36991"}, "batt_health": {"91% & Above": "84675", "86% - 90%": "84676", "85% & Below": "84677", "Battery Service": "84678"}, "housing": {"Grade A": "14077", "Grade B": "14078", "Grade C": "14079", "Defective": "26428"}, "screen": {"Grade A": "15529", "Grade B": "15530", "Grade C": "15531", "Defective": "27082"}, "accessories": {"Box": "36372", "Charging Cable": "36373", "Ear Phone": "36374", "Wall Charger": "36375"}}, {"deviceSpecId": "deviceSpecsId_8381", "deviceReqId": "5495", "name": "iPhone 7 Plus", "storage": {"32GB": "10308", "128GB": "10309", "256GB": "10310"}, "colour": {"Jet Black": "10311", "Black": "10312", "Silver": "10313", "Gold": "10314", "Rose Gold": "10315", "Red": "20955"}, "cop": {"Local Singapore Set": "36992", "Export Set": "36993"}, "batt_health": {"91% & Above": "84679", "86% - 90%": "84680", "85% & Below": "84681", "Battery Service": "84682"}, "housing": {"Grade A": "14080", "Grade B": "14081", "Grade C": "14082", "Defective": "26429"}, "screen": {"Grade A": "15532", "Grade B": "15533", "Grade C": "15534", "Defective": "27083"}, "accessories": {"Box": "36376", "Charging Cable": "36377", "Ear Phone": "36378", "Wall Charger": "36379"}}, {"deviceSpecId": "deviceSpecsId_134", "deviceReqId": "5043", "name": "iPhone SE", "storage": {"16GB": "158", "64GB": "159"}, "colour": {"Gold": "160", "Space Gray": "161", "Silver": "162", "Rose Gold": "163"}, "cop": {"Local Singapore Set": "36976", "Export Set": "36977"}, "batt_health": {"91% & Above": "84647", "86% - 90%": "84648", "85% & Below": "84649", "Battery Service": "84650"}, "housing": {"Grade A": "11814", "Grade B": "11815", "Grade C": "11816", "Defective": "25996"}, "screen": {"Grade A": "11817", "Grade B": "11818", "Grade C": "11819", "Defective": "26650"}, "accessories": {"Wall Charger": "44835", "Charging Cable": "44836", "Box": "44837", "Ear Phone": "44838"}}, {"deviceSpecId": "deviceSpecsId_94", "deviceReqId": "5041", "name": "iPhone 6s", "storage": {"16GB": "103", "32GB": "22049", "64GB": "104", "128GB": "105"}, "colour": {"Gold": "106", "Space Gray": "107", "Silver": "108", "Rose Gold": "109"}, "cop": {"Local Singapore Set": "36972", "Export Set": "36973"}, "batt_health": {"91% & Above": "84639", "86% - 90%": "84640", "85% & Below": "84641", "Battery Service": "84642"}, "housing": {"Grade A": "11786", "Grade B": "11787", "Grade C": "11788", "Defective": "25994"}, "screen": {"Grade A": "11789", "Grade B": "11790", "Grade C": "11791", "Defective": "26648"}, "accessories": {"Box": "36364", "Charging Cable": "36365", "Ear Phone": "36366", "Wall Charger": "36367"}}, {"deviceSpecId": "deviceSpecsId_116", "deviceReqId": "5042", "name": "iPhone 6s Plus", "storage": {"16GB": "133", "32GB": "22050", "64GB": "134", "128GB": "135"}, "colour": {"Gold": "136", "Space Gray": "137", "Silver": "138", "Rose Gold": "139"}, "cop": {"Local Singapore Set": "36974", "Export Set": "36975"}, "batt_health": {"91% & Above": "84643", "86% - 90%": "84644", "85% & Below": "84645", "Battery Service": "84646"}, "housing": {"Grade A": "11800", "Grade B": "11801", "Grade C": "11802", "Defective": "25995"}, "screen": {"Grade A": "11803", "Grade B": "11804", "Grade C": "11805", "Defective": "26649"}, "accessories": {"Box": "36368", "Charging Cable": "36369", "Ear Phone": "36370", "Wall Charger": "36371"}}, {"deviceSpecId": "deviceSpecsId_56", "deviceReqId": "5037", "name": "iPhone 6", "storage": {"16GB": "54", "64GB": "59", "128GB": "60"}, "colour": {"Gold": "55", "Space Gray": "56", "Silver": "57"}, "cop": {"Local Singapore Set": "36968", "Export Set": "36969"}, "batt_health": {"91% & Above": "84631", "86% - 90%": "84632", "85% & Below": "84633", "Battery Service": "84634"}, "housing": {"Grade A": "11659", "Grade B": "11661", "Grade C": "49386", "Defective": "49387"}, "screen": {"Grade A": "11662", "Grade B": "11664", "Grade C": "49388", "Defective": "49389"}, "accessories": {"Box": "36356", "Charging Cable": "36357", "Ear Phone": "36358", "Wall Charger": "36359"}}, {"deviceSpecId": "deviceSpecsId_75", "deviceReqId": "5040", "name": "iPhone 6 Plus", "storage": {"16GB": "79", "64GB": "80", "128GB": "11780"}, "colour": {"Gold": "81", "Space Gray": "82", "Silver": "83"}, "cop": {"Local Singapore Set": "36970", "Export Set": "36971"}, "batt_health": {"91% & Above": "84635", "86% - 90%": "84636", "85% & Below": "84637", "Battery Service": "84638"}, "housing": {"Grade A": "11781", "Grade B": "11782", "Grade C": "11783", "Defective": "25993"}, "screen": {"Grade A": "11704", "Grade B": "11711", "Grade C": "11717", "Defective": "26647"}, "accessories": {"Box": "36360", "Charging Cable": "36361", "Ear Phone": "36362", "Wall Charger": "36363"}}, {"deviceSpecId": "deviceSpecsId_153", "deviceReqId": "5044", "name": "iPhone 5S", "storage": {"16GB": "183", "32GB": "184", "64GB": "185"}, "colour": {"Gold": "186", "Space Gray": "187", "Silver": "188"}, "cop": {"Local Singapore Set": "36978", "Export Set": "36979"}, "batt_health": {"91% & Above": "84651", "86% - 90%": "84652", "85% & Below": "84653", "Battery Service": "84654"}, "housing": {"Grade A": "11768", "Grade B": "11769", "Grade C": "11770", "Defective": "25997"}, "screen": {"Grade A": "11771", "Grade B": "11772", "Grade C": "11773", "Defective": "26651"}, "accessories": {"Wall Charger": "44839", "Charging Cable": "44840", "Box": "44841", "Ear Phone": "44842"}}]}
# for product in productDict["products"]:
#     for storage in product["storage"].items():
#         with open(f'{filename} - Price Matrix.csv', 'a') as inFile:
#             inFile.write('\n')
#         for batt_health in product["batt_health"].items():
#             if batt_health[0] == "Battery Service":
#                 continue
#             for housing in product["housing"].items():
#                 if housing[0] == 'Grade C' or housing[0] == 'Defective':
#                     continue
#                 # print(f'{product["deviceReqId"]} | {storage[1]} | {batt_health[1]} | {housing[1]} | {product["accessories"]["Charging Cable"]}, {product["accessories"]["Box"]}')
#
#                 tempStorage = storage[0]
#                 price = getSellUpPrices(product["deviceReqId"],storage[1], list(product["colour"].values())[0], list(product["cop"].values())[0], list(product["housing"].values())[0], list(product["screen"].values())[0], batt_health[1], [product["accessories"]["Charging Cable"], product["accessories"]["Box"]])
#                 print(f'${price} - {product["name"]} | {storage[0]} | {batt_health[0]} | {housing[0]} | Full Set')
#                 # print(price, end=' ')
#                 with open(f'{filename} - Price Matrix.csv', 'a') as inFile:
#                     inFile.write(f'{str(price)}, ')
#                 price = getSellUpPrices(product["deviceReqId"],storage[1], list(product["colour"].values())[0], list(product["cop"].values())[0], list(product["housing"].values())[0], list(product["screen"].values())[0], batt_health[1], False)
#                 print(f'${price} - {product["name"]} | {storage[0]} | {batt_health[0]} | {housing[0]} | No accessory')
#                 # print(price, end=' ')
#                 with open(f'{filename} - Price Matrix.csv', 'a') as inFile:
#                     inFile.write(f'{str(price)}, ')

                # for accessories in product["accessories"]:
                #     print(f'{product["name"]} | {storage[0]}, {storage[1]} | {batt_health} | {housing} | {accessories}')

# if __name__ == '__main__':
#     updateProductDict('productDict.json')

