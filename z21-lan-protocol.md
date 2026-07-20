Z21 LAN Protokoll Spezifikation 



# **Z21 LAN Protokoll Spezifikation** 

Dokumentenversion 1.13 

1/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **Rechtliches, Haftungsausschluss** 

Die Firma Modelleisenbahn GmbH erklärt ausdrücklich, in keinem Fall für den Inhalt in diesem Dokument oder für in diesem Dokument angegebene weiterführende Informationen rechtlich haftbar zu sein. 

Die Rechtsverantwortung liegt ausschließlich beim Verwender der angegebenen Daten oder beim Herausgeber der jeweiligen weiterführenden Information. 

Für sämtliche Schäden die durch die Verwendung der angegebenen Informationen oder durch die NichtVerwendung der angegebenen Informationen entstehen übernimmt die Modelleisenbahn GmbH, Plainbachstraße 4, A-5101 Bergheim, Austria, ausdrücklich keinerlei Haftung. 

Die Modelleisenbahn GmbH, Plainbachstraße 4, A-5101 Bergheim, Austria, übernimmt keinerlei Gewähr für die Aktualität, Korrektheit, Vollständigkeit oder Qualität der bereitgestellten Informationen. Haftungsansprüche, welche sich auf Schäden materieller, immaterieller oder ideeller Art beziehen, die durch die Nutzung oder Nichtnutzung der dargebotenen Informationen verursacht wurden, sind grundsätzlich ausgeschlossen. 

Die Modelleisenbahn GmbH, Plainbachstraße 4, A-5101 Bergheim, Austria, behält es sich vor, die bereit gestellten Informationen ohne gesonderte Ankündigung zu verändern, zu ergänzen oder zu löschen. 

Alle innerhalb des Dokuments genannten und gegebenenfalls durch Dritte geschützten Marken- und Warenzeichen unterliegen uneingeschränkt den Bestimmungen des jeweils gültigen Kennzeichenrechts und den Besitzrechten der jeweiligen eingetragenen Eigentümer. 

Das Copyright für veröffentlichte, von der Modelleisenbahn GmbH, Plainbachstraße 4, A-5101 Bergheim, Austria, erstellte Informationen, bleibt in jedem Fall allein bei der Modelleisenbahn GmbH, Plainbachstraße 4, A-5101 Bergheim, Austria. 

Eine Vervielfältigung oder Verwendung der bereit gestellten Informationen in anderen elektronischen oder gedruckten Publikationen ist ohne ausdrückliche Zustimmung nicht gestattet. 

Sollten Teile oder einzelne Formulierungen des Haftungsausschlusses der geltenden Rechtslage nicht, nicht mehr oder nicht vollständig entsprechen, bleiben die übrigen Teile des Haftungsausschlusses in ihrem Inhalt und ihrer Gültigkeit davon unberührt. 

## **Impressum** 

Apple, iPad, iPhone, iOS are trademarks of Apple Inc., registered in the U.S. and other countries. App Store is a service mark of Apple Inc. Android is a trademark of Google Inc. Google Play is a service mark of Google Inc. 

RailCom und XpressNet sind eingetragene Warenzeichen der Firma Lenz Elektronik GmbH. Motorola is a registered trademark of Motorola Inc., Tempe-Phoenix, USA. LocoNet is a registered trademark of Digitrax, Inc. 

Alle Rechte, Änderungen, Irrtümer und Liefermöglichkeiten vorbehalten. Spezifikationen und Abbildungen ohne Gewähr. Änderung vorbehalten. 

_Herausgeber: Modelleisenbahn GmbH, Plainbachstraße 4, A-5101 Bergheim, Austria_ 

Dokumentenversion 1.13 

2/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **Änderungshistorie** 

|Datum|Dokumentenversion|Änderung|
|---|---|---|
|06.02.2013|1.00|Beschreibung der LAN Schnittstelle für<br>Z21 FW Version 1.10, 1.11<br>und SmartRail FW Version 1.12|
|20.03.2013|1.01|Z21 FW Version 1.20<br>LAN_SET_BROADCASTFLAGS: neue Flags<br>LAN_GET_HWINFO: neuer Befehl<br>LAN_SET_TURNOUTMODE: MM-Format<br>LocoNet: Gateway Funktionalität|
|||SmartRail FW Version 1.13<br>LAN_GET_HWINFO: neuer Befehl|
|29.10.2013|1.02|**Z21 FW Version 1.22:**<br>**Decoder CV Lesen und Schreiben**<br>POM Lesen und Accessory Decoder: neue Befehle<br>**LocoNet Dispatch und Gleisbesetztmelder**<br>_LAN_LOCONET_DISPATCH_ADDR_: neu Antwort<br>LAN_SET_BROADCASTFLAGS: neues Flag<br>LAN_LOCONET_DETECTOR: neuer Befehl|
|12.02.2014|1.03|**Z21 FW Version 1.23**<br>Korrektur lange Fahrzeugadresse in Kapitel 4 Fahren<br>LAN_X_MM_WRITE_BYTE<br>LAN_LOCONET_DETECTOR: Erweiterung für LISSY|
|25.03.2014|1.04|<br>**Z21 FW Version 1.24**<br>LAN_SET_BROADCASTFLAGS: Flag 0x00010000<br>Kapitel 5 Schalten: Erklärung Weichenadressierung<br>LAN_X_GET_TURNOUT_INFO: Erweiterung Queue-Bit<br>LAN_X_DCC_WRITE_REGISTER|
|21.01.2015|1.05|**Z21 FW Version 1.25 und 1.26**<br>Kapitel 4 Fahren: Erklärungen Fahrstufen und Format<br>LAN_X_DCC_READ_REGISTER<br>LAN_X_DCC_WRITE_REGISTER<br>LAN_LOCONET_Z21_TX Binary State Control Instruction|
|05.04.2016|1.06|**Z21 FW Version 1.28**<br>Kapitel 2 System Status Versionen: z21start<br>LAN_GET_HW_INFO<br>LAN_GET_CODE|
|19.04.2017|1.07|<br>**Z21 FW Version 1.29 und 1.30**<br>Kapitel 8 RailCom|
|||Kapitel 10 CAN: Belegtmelder|
|15.01.2018|1.08|Kapitel 9 LocoNet: LissyBeispiele|
|23.05.2019|1.09|Kapitel 4 Fahren: Codierung der Geschwindigkeitsstufen<br>Kapitel 7 R-BUS: 10808 und 10819 hinzugefügt<br>Kapitel 9.3.1: Korrektur Binary State Control Instruction|
|28.01.2021|1.10|**Z21 FW Version 1.40**<br>Kapitel 2 LAN_GET_HWINFO: weitere HW-Typen<br>Kapitel 5 Schalten: Erweiterte Zubehördecoder DCCext<br>Kapitel 11 zLink|
|11.08.2021|1.11|<br>**Z21 FW Version 1.41**<br>Kapitel 10 CAN: Booster|
|28.02.2022|1.12|<br>**Z21 FW Version 1.42**<br>Kapitel 2.18 SystemState: cseRCN213, Capabilities<br>Kapitel 4: DCC Funktionen ≥ F29, Binary States<br>Kapitel 6: Tippfehler POM Read „111001MM“ 0xE4 ausgebessert<br>Kapitel 10.2 und 11.2: Booster Management|
|20.06.2023|1.13|**Z21 FW Version 1.43**<br>Kapitel 4 Fahren: Motorola-Bit in LAN_X_LOCO_INFO<br>Kapitel 4 Fahren: neue Befehle für Purge und E-STOP<br>Kapitel 12 Modellzeit|



Dokumentenversion 1.13 

3/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **Inhaltsverzeichnis** 

|**1**<br>|**GRUNDLAGEN ..................................................................................................................................... 8**|
|---|---|
|**1.1**|**Kommunikation .............................................................................................................................................. 8**|
|**1.2**|**Z21 Datensatz .................................................................................................................................................. 8**|
|1.2|.1<br>Aufbau ....................................................................................................................................................... 8|
|1.2|.2<br>X-BUS Protokoll Tunnelung ..................................................................................................................... 9|
|1.2|.3<br>LocoNet Tunnelung .................................................................................................................................. 9|
|**1.3**|**Kombinieren von Datensätzen in einem UDP-Paket.................................................................................. 10**|
|**2**<br>|**SYSTEM, STATUS, VERSIONEN ...................................................................................................... 11**|
|**2.1**|**LAN_GET_SERIAL_NUMBER ................................................................................................................. 11**|
|**2.2**|**LAN_LOGOFF ............................................................................................................................................. 11**|
|**2.3**|**LAN_X_GET_VERSION ............................................................................................................................. 11**|
|**2.4**|**LAN_X_GET_STATUS ............................................................................................................................... 12**|
|**2.5**|**LAN_X_SET_TRACK_POWER_OFF ....................................................................................................... 12**|
|**2.6**|**LAN_X_SET_TRACK_POWER_ON......................................................................................................... 12**|
|**2.7**|**LAN_X_BC_TRACK_POWER_OFF......................................................................................................... 13**|
|**2.8**|**LAN_X_BC_TRACK_POWER_ON........................................................................................................... 13**|
|**2.9**|**LAN_X_BC_PROGRAMMING_MODE ................................................................................................... 13**|
|**2.10**|**LAN_X_BC_TRACK_SHORT_CIRCUIT ................................................................................................ 13**|
|**2.11**|**LAN_X_UNKNOWN_COMMAND ............................................................................................................ 14**|
|**2.12**|**LAN_X_STATUS_CHANGED.................................................................................................................... 14**|
|**2.13**|**LAN_X_SET_STOP ..................................................................................................................................... 15**|
|**2.14**|**LAN_X_BC_STOPPED ............................................................................................................................... 15**|
|**2.15**|**LAN_X_GET_FIRMWARE_VERSION .................................................................................................... 15**|
|**2.16**|**LAN_SET_BROADCASTFLAGS .............................................................................................................. 16**|
|**2.17**|**LAN_GET_BROADCASTFLAGS .............................................................................................................. 17**|
|**2.18**|**LAN_SYSTEMSTATE_DATACHANGED ............................................................................................... 18**|
|**2.19**|**LAN_SYSTEMSTATE_GETDATA ........................................................................................................... 19**|



Dokumentenversion 1.13 

4/78 

06.11.2023 



|Z21 LAN Protokoll Spezifikation|
|---|
|**2.20**<br>**LAN_GET_HWINFO ................................................................................................................................... 19**|
|**2.21**<br>**LAN_GET_CODE ........................................................................................................................................ 20**|
|**3**<br>**EINSTELLUNGEN .............................................................................................................................. 21**|
|**3.1**<br>**LAN_GET_LOCOMODE ............................................................................................................................ 21**|
|**3.2**<br>**LAN_SET_LOCOMODE ............................................................................................................................. 21**|
|**3.3**<br>**LAN_GET_TURNOUTMODE.................................................................................................................... 22**|
|**3.4**<br>**LAN_SET_TURNOUTMODE .................................................................................................................... 22**|
|**4**<br>**FAHREN ............................................................................................................................................. 23**|
|**4.1**<br>**LAN_X_GET_LOCO_INFO ....................................................................................................................... 23**|
|**4.2**<br>**LAN_X_SET_LOCO_DRIVE ..................................................................................................................... 24**|
|**4.3**<br>**Funktionen für Fahrzeugdecoder ................................................................................................................ 25**|
|4.3.1<br>LAN_X_SET_LOCO_FUNCTION ........................................................................................................ 25|
|4.3.2<br>LAN_X_SET_LOCO_FUNCTION_GROUP ........................................................................................ 26|
|4.3.3<br>LAN_X_SET_LOCO_BINARY_STATE .............................................................................................. 27|
|**4.4**<br>**LAN_X_LOCO_INFO .................................................................................................................................. 28**|
|**4.5**<br>**LAN_X_SET_LOCO_E_STOP ................................................................................................................... 29**|
|**4.6**<br>**LAN_X_PURGE_LOCO .............................................................................................................................. 29**|
|**5**<br>**SCHALTEN ......................................................................................................................................... 30**|
|**5.1**<br>**LAN_X_GET_TURNOUT_INFO ............................................................................................................... 31**|
|**5.2**<br>**LAN_X_SET_TURNOUT ............................................................................................................................ 31**|
|5.2.1<br>LAN_X_SET_TURNOUT mit Q=0 ....................................................................................................... 31|
|5.2.2<br>LAN_X_SET_TURNOUT mit Q=1 ....................................................................................................... 33|
|**5.3**<br>**LAN_X_TURNOUT_INFO.......................................................................................................................... 34**|
|**5.4**<br>**LAN_X_SET_EXT_ACCESSORY ............................................................................................................. 35**|
|**5.5**<br>**LAN_X_GET_EXT_ACCESSORY_INFO ................................................................................................ 36**|
|**5.6**<br>**LAN_X_EXT_ACCESSORY_INFO ........................................................................................................... 36**|
|**6**<br>**DECODER CV LESEN UND SCHREIBEN ........................................................................................ 37**|
|**6.1**<br>**LAN_X_CV_READ ...................................................................................................................................... 37**|
|**6.2**<br>**LAN_X_CV_WRITE .................................................................................................................................... 37**|
|**6.3**<br>**LAN_X_CV_NACK_SC ............................................................................................................................... 37**|
|**6.4**<br>**LAN_X_CV_NACK ...................................................................................................................................... 38**|



Dokumentenversion 1.13 

5/78 

06.11.2023 



|Z21 LAN Protokoll Spezifikation|
|---|
|**6.5**<br>**LAN_X_CV_RESULT .................................................................................................................................. 38**|
|**6.6**<br>**LAN_X_CV_POM_WRITE_BYTE ............................................................................................................ 39**|
|**6.7**<br>**LAN_X_CV_POM_WRITE_BIT ................................................................................................................ 39**|
|**6.8**<br>**LAN_X_CV_POM_READ_BYTE .............................................................................................................. 40**|
|**6.9**<br>**LAN_X_CV_POM_ACCESSORY_WRITE_BYTE ................................................................................. 41**|
|**6.10**<br>**LAN_X_CV_POM_ ACCESSORY_WRITE_BIT .................................................................................... 41**|
|**6.11**<br>**LAN_X_CV_POM_ ACCESSORY_READ_BYTE ................................................................................... 42**|
|**6.12**<br>**LAN_X_MM_WRITE_BYTE ..................................................................................................................... 43**|
|**6.13**<br>**LAN_X_DCC_READ_REGISTER ............................................................................................................. 44**|
|**6.14**<br>**LAN_X_DCC_WRITE_REGISTER........................................................................................................... 44**|
|**7**<br>**RÜCKMELDER – R-BUS ................................................................................................................... 45**|
|**7.1**<br>**LAN_RMBUS_DATACHANGED .............................................................................................................. 45**|
|**7.2**<br>**LAN_RMBUS_GETDATA .......................................................................................................................... 45**|
|**7.3**<br>**LAN_RMBUS_PROGRAMMODULE ....................................................................................................... 46**|
|**8**<br>**RAILCOM ............................................................................................................................................ 47**|
|**8.1**<br>**LAN_RAILCOM_DATACHANGED ......................................................................................................... 47**|
|**8.2**<br>**LAN_RAILCOM_GETDATA ..................................................................................................................... 48**|
|**9**<br>**LOCONET ........................................................................................................................................... 49**|
|**9.1**<br>**LAN_LOCONET_Z21_RX .......................................................................................................................... 50**|
|**9.2**<br>**LAN_LOCONET_Z21_TX .......................................................................................................................... 50**|
|**9.3**<br>**LANLOCONETFROMLAN .................................................................................................................. 51**|
|**___**<br>9.3.1<br>DCC Binary State Control Instruction per LocoNet OPC_IMM_PACKET ........................................... 51|
|**9.4**<br>**LAN_LOCONET_DISPATCH_ADDR ...................................................................................................... 52**|
|**9.5**<br>**LAN_LOCONET_DETECTOR .................................................................................................................. 53**|
|**10**<br>**CAN ................................................................................................................................................. 57**|
|**10.1**<br>**LAN_CAN_DETECTOR ............................................................................................................................. 57**|
|**10.2**<br>**CAN Booster .................................................................................................................................................. 59**|
|10.2.1<br>LAN_CAN_DEVICE_GET_DESCRIPTION ........................................................................................ 59|
|10.2.2<br>LAN_CAN_DEVICE_SET_DESCRIPTION ......................................................................................... 59|
|10.2.3<br>LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD ............................................................................... 60<br>10.2.4<br>LAN_CAN_BOOSTER_SET_TRACKPOWER .................................................................................... 61|



Dokumentenversion 1.13 

6/78 

06.11.2023 



|Z21 LAN Protokoll Spezifikation|
|---|
|**11**<br>**ZLINK .............................................................................................................................................. 62**|
|**11.1**<br>**Adapter .......................................................................................................................................................... 62**|
|11.1.1<br>10838 Z21 pro LINK .............................................................................................................................. 62|
|11.1.1.1<br>LAN_ZLINK_GET_HWINFO ....................................................................................................... 63|
|**11.2**<br>**Booster 10806, 10807 und 10869 .................................................................................................................. 64**|
|11.2.1<br>LAN_BOOSTER_GET_DESCRIPTION ............................................................................................... 64|
|11.2.2<br>LAN_BOOSTER_SET_DESCRIPTION ............................................................................................... 64|
|11.2.3<br>LAN_BOOSTER_SYSTEMSTATE_GETDATA .................................................................................. 65|
|11.2.4<br>LAN_BOOSTER_SYSTEMSTATE_DATACHANGED ...................................................................... 65|
|11.2.5<br>LAN_BOOSTER_SET_POWER ........................................................................................................... 66|
|**11.3**<br>**Decoder 10836 und 10837 ............................................................................................................................. 67**|
|11.3.1<br>LAN_DECODER_GET_DESCRIPTION .............................................................................................. 67|
|11.3.2<br>LAN_DECODER_SET_DESCRIPTION ............................................................................................... 67|
|11.3.3<br>LAN_DECODER_SYSTEMSTATE_GETDATA ................................................................................. 67|
|11.3.4<br>LAN_DECODER_SYSTEMSTATE_DATACHANGED ..................................................................... 68|
|11.3.4.1<br>SwitchDecoderSystemState............................................................................................................. 68|
|11.3.4.2<br>SignalDecoderSystemState ............................................................................................................. 70|
|**12**<br>**MODELLZEIT .................................................................................................................................. 71**|
|**12.1**<br>**LAN_FAST_CLOCK_CONTROL ............................................................................................................. 71**|
|12.1.1<br>Modellzeit lesen ...................................................................................................................................... 71|
|12.1.2<br>Modellzeit setzen .................................................................................................................................... 71|
|12.1.3<br>Modellzeit starten .................................................................................................................................... 72|
|12.1.4<br>Modellzeit anhalten ................................................................................................................................. 72|
|**12.2**<br>**LAN_FAST_CLOCK_DATA ...................................................................................................................... 73**|
|**12.3**<br>**LAN_FAST_CLOCK_SETTINGS_GET ................................................................................................... 74**|
|**12.4**<br>**LAN_FAST_CLOCK_SETTINGS_SET .................................................................................................... 75**|
|**ANHANG A – BEFEHLSÜBERSICHT ...................................................................................................... 76**|
|**Client an Z21 ............................................................................................................................................................. 76**|
|**Z21 an Client ............................................................................................................................................................. 77**|
|**ABBILDUNGSVERZEICHNIS ................................................................................................................... 78**|
|**TABELLENVERZEICHNIS ........................................................................................................................ 78**|



Dokumentenversion 1.13 

7/78 

06.11.2023 





<!-- Start of picture text -->
!<br>|\<br>|Seriennummer anfordern<br>| j<br>system-Stat<br>KK——Swstemstaus____{gystem-staus |<br>| broadcast | System-Status(broadcast) |<br>je| (broadcast)LokinfoOinto #3#3} TT Lokinfo#S |<br>| \ (broadcast)<br>|\<br>'Hl<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



### **1.2.2 X-BUS Protokoll Tunnelung** 

Mit dem Z21-LAN-Header **0x40** ( **_LAN_X__** _xxx_ ) werden Anforderungen und Antworten übertragen, welche an das X-BUS-Protokoll _angelehnt_ sind. Gemeint ist dabei nur das Protokoll, denn diese Befehle haben nichts mit dem physikalischen X-BUS der Z21 zu tun, sondern sind ausschließlich an die LAN-Clients bzw. die Z21 gerichtet. 

Der eigentliche X-BUS-Befehl liegt dann im Feld **Data** innerhalb des Z21-Datensatzes. Das letzte Byte ist eine Prüfsumme und wird als XOR über den X-BUS-Befehl berechnet. Beispiel: 

|**DataLe**|**n**|**Header**|**Data**||||
|---|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**DB1**|**XOR-Byte**|
|0x08|0x00|**0x40**<br>0x00|**h**|**x**|**y**|h XOR x XORy|



### **1.2.3 LocoNet Tunnelung** 

### **Ab Z21 FW Version 1.20.** 

Mit dem Z21-LAN-Header **0xA0 und 0xA1** ( **_LAN_LOCONET_Z21_RX, LAN_LOCONET_Z21_TX_** ) werden Meldungen, die von der Z21 am LocoNet-Bus empfangen bzw. gesendet werden, an den LANClient weitergeleitet. Der LAN-Client muss dazu die LocoNet-Meldungen mittels **_2.16_** LAN_SET_BROADCASTFLAGS abonniert haben. 

Über den  Z21-LAN-Header **0xA2 (LAN_LOCONET_FROM_LAN** ) kann der LAN-Client Meldungen auf den LocoNet-Bus schreiben. 

Damit kann die Z21 als **Ethernet/LocoNet Gateway** verwendet werden, wobei die Z21 gleichzeitig der LocoNet-Master ist, welcher die Refresh-Slots verwaltet und die DCC-Pakete generiert. 

Die eigentliche LocoNet-Meldung liegt jeweils im Feld **Data** innerhalb des Z21-Datensatzes. 

Beispiel LocoNet-Meldung OPC_MOVE_SLOTS <0><0> („DISPATCH_GET“) wurde von Z21 empfangen: 

|**DataLe**|**n**|**Header**|**Data**||||
|---|---|---|---|---|---|---|
||||**OPC**|**ARG1**|**ARG2**|**CKSUM**|
|0x08|0x00|**0xA0**<br>0x00|**0xBA**|**0x00**|**0x00**|**0x45**|



Mehr zum Thema LocoNet-Gateway finden Sie im Abschnitt **_9_** LocoNet. 

Dokumentenversion 1.13 

9/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_1.3 Kombinieren von Datensätzen in einem UDP-Paket_** 

In den Nutzdaten eines UDP-Paket können auch mehrere, von einander unabhängige Z21-Datensätze gemeinsam an einen Empfänger gesendet werden. Jeder Empfänger muss diese kombinierten UDPPakete interpretieren können. 

### **Beispiel** 

Folgendes kombinierte UDP Paket... 

|**UDP Paket**<br>**IP Header**|<br>**UDP Header**|**UDP Nutzdaten**|||
|---|---|---|---|---|
|||**Z21 Datensatz 1**|**Z21 Datensatz 2**|**Z21 Datensatz 3**|
|||LAN_X_GET_TOURNOUT_INFO #4|LAN_X_GET_TOURNOUT_INFO #5|LAN_RMBUS_GETDATA #0|



... ist gleichwertig mit diesen drei hintereinander gesendeten UDP-Paketen: 

|**UDP Paket**<br>|**1**<br>||
|---|---|---|
|**IP Header**|**UDP Header**|**UDP Nutzdaten**|
|||**Z21 Datensatz**|
|||LAN_X_GET_TOURNOUT_INFO #4|
|**UDP Paket**<br>|**2**<br>||
|**IP Header**|**UDP Header**|**UDP Nutzdaten**|
|||**Z21 Datensatz**|
|||LAN_X_GET_TOURNOUT_INFO #5|
|**UDP Paket**<br>|**3**<br>||
|**IP Header**|**UDP Header**|**UDP Nutzdaten**|
|||**Z21 Datensatz**|
|||LAN_RMBUS_GETDATA #0|



Das UDP Paket muss in eine Ethernet MTU passen, d.h. es stehen abzüglich IPv4 Header und UDPHeader maximal 1500-20-8 = 1472 Bytes Nutzdaten übrig. 

Dokumentenversion 1.13 

10/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **2 System, Status, Versionen** 

### **_2.1 LAN_GET_SERIAL_NUMBER_** 

Auslesen der Seriennummer der Z21. 

<u>Anforderung an Z21:</u> 

|<br>**DataLe**|<br>**n**|<br>**Header**|**Data**|
|---|---|---|---|
|0x04|0x00|**0x10**<br>0x00|-|
|Antwor|t von Z21|:||
|**DataLe**|**n**|**Header**|**Data**|
|0x08|0x00|**0x10**<br>0x00|Seriennummer 32 Bit (little endian)|



### **_2.2 LAN_LOGOFF_** 

Abmelden des Clients von der Z21. 

<u>Anforderung an Z21:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|0x04|0x00|**0x30**|0x00|-|



Antwort von Z21: keine 

Verwenden Sie beim Abmelden die gleiche Portnummer wie beim Anmelden. 

**Anmerkung** : das Anmelden erfolgt implizit mit dem ersten Befehl des Clients (z.B. _LAN_SYSTEM_STATE_GETDATA_ , ...). 

### **_2.3 LAN_X_GET_VERSION_** 

Mit folgendem Kommando kann die X-Bus Version der Z21 ausgelesen werden. 

<u>Anforderung an Z21:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x21**|**0x21**|0x00|



<u>Antwort von Z21:</u> 

|**DataLen**|**Header**|**Data**|||||
|---|---|---|---|---|---|---|
|||**X-Header**|**DB0**|**DB1**|**DB2**|**XOR-Byte**|
|0x09<br>0x00|**0x40**<br>0x00|0x63|0x21|**XBUS_VER**|**CMDST_ID**|0x60|



**XBUS_VER** X-Bus Protokoll Version (0x30 = V3.0, 0x36 = V3.6, 0x40 = V4.0, … ) **CMDST_ID** Command station ID (0x12 = Z21 Gerätefamilie) 

Dokumentenversion 1.13 

11/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.4 LAN_X_GET_STATUS_** 

Mit diesem Kommando kann der Zentralenstatus angefordert werden. 

|Anforde<br>**DataLe**|rung an Z<br>**n**|21:<br>**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x21**|**0x24**|0x05|



Antwort von Z21: siehe _2.12_ LAN_X_STATUS_CHANGED 

Dieser Zentralenstatus ist identisch mit dem CentralState, welcher im SystemStatus geliefert wird, siehe _2.18_ LAN_SYSTEMSTATE_DATACHANGED. 

### **_2.5 LAN_X_SET_TRACK_POWER_OFF_** 

Mit diesem Kommando wird die Gleisspannung abgeschaltet. 

|Anforderung an Z|21:||||
|---|---|---|---|---|
|**DataLen**|**Header**|**Data**|||
|||**X-Header**|**DB0**|**XOR-Byte**|
|0x07<br>0x00|**0x40**<br>0x00|**0x21**|**0x80**|0xa1|



Antwort von Z21: siehe _2.7_ LAN_X_BC_TRACK_POWER_OFF 

### **_2.6 LAN_X_SET_TRACK_POWER_ON_** 

Mit diesem Kommando wird die Gleisspannung eingeschaltet, bzw. der Notstop oder Programmiermodus beendet. 

|Anforde<br>**DataLe**|rung an Z<br>**n**|21:<br>**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x21**|**0x81**|0xa0|



Antwort von Z21: 

siehe _2.8_ LAN_X_BC_TRACK_POWER_ON 

Dokumentenversion 1.13 

12/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.7 LAN_X_BC_TRACK_POWER_OFF_** 

Folgendes Paket wird von der Z21 an die registrierten Clients versendet, wenn 

- ein Client den Befehl _2.5_ LAN_X_SET_TRACK_POWER_OFF abgeschickt hat 

- durch ein anderes Eingabegerät (multiMaus) die Gleisspannung abgeschaltet worden ist. 

- der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

### <u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x61**|**0x00**|0x61|



### **_2.8 LAN_X_BC_TRACK_POWER_ON_** 

Folgendes Paket wird von der Z21 an die registrierten Clients versendet, wenn 

- ein Client den Befehl _2.6_ LAN_X_SET_TRACK_POWER_ON abgeschickt hat. 

- durch ein anderes Eingabegerät (multiMaus) die Gleisspannung eingeschaltet worden ist. 

- der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

<u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x61**|**0x01**|0x60|



### **_2.9 LAN_X_BC_PROGRAMMING_MODE_** 

Folgendes Paket wird von der Z21 an die registrierten Clients versendet, wenn die Z21 durch **_6.1_** LAN_X_CV_READ oder **_6.2_** LAN_X_CV_WRITE in den CV-Programmiermodus versetzt worden ist und der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

<u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x61**|**0x02**|0x63|



### **_2.10 LAN_X_BC_TRACK_SHORT_CIRCUIT_** 

Folgendes Paket wird von der Z21 an die registrierten Clients versendet, wenn ein Kurzschluss aufgetreten ist und der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

<u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x61**|**0x08**|0x69|



Dokumentenversion 1.13 

13/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.11 LAN_X_UNKNOWN_COMMAND_** 

Folgendes Paket wird von der Z21 an den Client als Antwort auf eine ungültige Anforderung versendet. 

<u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x61**|**0x82**|E3|



### **_2.12 LAN_X_STATUS_CHANGED_** 

Folgendes Paket wird von der Z21 an den Client versendet, wenn der Client den Status explizit mit _2.4_ LAN_X_GET_STATUS angefordert hat. 

### <u>Z21 an Client:</u> 

|**DataLen**|**Header**|**Data**||||
|---|---|---|---|---|---|
|||**X-Header**|**DB0**|**DB1**|**XOR-Byte**|
|0x08<br>0x00|**0x40**<br>0x00|**0x62**|**0x22**|**Status**|XOR-Byte|



DB1 … Zentralenstatus 

Bitmasken für Zentralenstatus: `#define csEmergencyStop 0x01 // Der Nothalt ist eingeschaltet #define csTrackVoltageOff 0x02 // Die Gleisspannung ist abgeschaltet #define csShortCircuit 0x04 // Kurzschluss #define csProgrammingModeActive 0x20 // Der Programmiermodus ist aktiv` 

Dieser Zentralenstatus ist identisch mit dem SystemState.CentralState, siehe _2.18_ LAN_SYSTEMSTATE_DATACHANGED _._ 

Dokumentenversion 1.13 

14/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.13 LAN_X_SET_STOP_** 

Mit diesem Kommando wird der Notstop aktiviert, d.h. die Loks werden angehalten aber die Gleisspannung bleibt eingeschaltet. 

|Anforderung an Z|21:|||
|---|---|---|---|
|**DataLen**|**Header**|**Data**||
|||**X-Header**|**XOR-Byte**|
|0x06<br>0x00|**0x40**<br>0x00|**0x80**|0x80|



Antwort von Z21: siehe _2.14_ LAN_X_BC_STOPPED 

### **_2.14 LAN_X_BC_STOPPED_** 

Folgendes Paket wird von der Z21 an die registrierten Clients versendet, wenn 

- ein Client den Befehl _2.13_ LAN_X_SET_STOP abgeschickt hat. 

- durch ein anderes Eingabegerät (multiMaus) der Notstop ausgelöst worden ist. 

- • der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

|Z21 an|Client:|||||
|---|---|---|---|---|---|
|**DataLe**|**n**|**Header**|**Data**|||
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x81**|0x00|0x81|



### **_2.15 LAN_X_GET_FIRMWARE_VERSION_** 

Mit diesem Kommando kann die Firmware-Version der Z21 ausgelesen werden. 

|Anforde|rung an Z|21:||||
|---|---|---|---|---|---|
|**DataLe**|**n**|**Header**|**Data**|||
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0xF1**|0x0A|0xFB|



<u>Antwort von Z21:</u> 

|**DataLe**|**n**|**Header**|**Data**|||||
|---|---|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**DB1**|**DB2**|**XOR-Byte**|
|0x09|0x00|**0x40**<br>0x00|0xF3|0x0A|**V_MSB**|**V_LSB**|XOR-Byte|



**DB1** … Höherwertiges Byte der Firmware Version **DB2** … Niederwertiges Byte der Firmware Version 

Die Version wird im BCD-Format angegeben. Beispiel: `0x09 0x00 0x40 0x00 0xf3 0x0a` **`0x01 0x23`** `0xdb` bedeutet: „Firmware Version **1.23** “ 

Dokumentenversion 1.13 

15/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.16 LAN_SET_BROADCASTFLAGS_** 

Setzen der Broadcast-Flags in der Z21. Diese Flags werden pro Client (d.h. pro IP + Portnummer) eingestellt und müssen beim nächsten Anmelden wieder neu gesetzt werden. 

### <u>Anforderung an Z21:</u> 

|<br>**DataLen**|<br>**Header**<br>**Data**|
|---|---|
|0x08<br>0x00|**0x50**<br>0x00<br>Broadcast-Flags 32 Bit (little endian)|
|Broadcast-Fla<br>0x00000001<br>0x00000002<br>0x00000004<br>0x00000100|gs ist eine OR-Verknüpfung der folgenden Werte:<br>Automatisch generierte Broadcasts und Meldungen, die das Fahren und Schalten<br>betreffen, werden an den registrierten Client zugestellt.<br>Folgende Meldungen werden hier abonniert:<br>**_2.7_**LAN_X_BC_TRACK_POWER_OFF<br>**_2.8_**LAN_X_BC_TRACK_POWER_ON<br>**_2.9_**LAN_X_BC_PROGRAMMING_MODE<br>**_2.10_**LAN_X_BC_TRACK_SHORT_CIRCUIT<br>**_2.14_**LAN_X_BC_STOPPED<br>**_4.4_**LAN_X_LOCO_INFO (die betreffende Lok-Adresse muss ebenfalls abonniert sein)<br>**_5.3_**LAN_X_TURNOUT_INFO<br>Änderungen der Rückmelder am R-Bus werden automatisch gesendet.<br>Broadcast Meldung der Z21 siehe**_7.1_**LAN_RMBUS_DATACHANGED<br>Änderungen bei RailCom-Daten der abonnierten Loks werden automatisch gesendet.<br>Broadcast Meldung der Z21 siehe**8.1**LAN_RAILCOM_DATACHANGED<br>Änderungen des Z21-Systemzustands werden automatisch gesendet.<br>Broadcast Meldung der Z21 siehe**_2.18_**LAN_SYSTEMSTATE_DATACHANGED|
|**Ab Z21 FW V**<br>0x00010000|**ersion 1.20:**<br>Ergänzt Flag 0x00000001; Client bekommt nun LAN_X_LOCO_INFO, ohne vorher die<br>entsprechenden Lok-Adressen abonnieren zu müssen, d.h. für alle gesteuerten Loks!<br>Dieses Flag darf aufgrund des hohen Netzwerkverkehrs nur von vollwertigen<br>PC-Steuerungen verwendet werden und ist keinesfalls für mobile Handregler gedacht.<br>Ab FW V1.20 bis V1.23: LAN_X_LOCO_INFO wird für**alle**Loks versendet.<br>Ab**FW V1.24**:<br>LAN_X_LOCO_INFO wird für**alle geänderten**Loks versendet.|
|0x01000000<br>0x02000000|Meldungen vom**LocoNet**-Bus an LAN Client weiterleiten ohne Loks und Weichen.<br>Lok-spezifische**LocoNet**-Meldungen an LAN Client weiterleiten:<br>OPC_LOCO_SPD, OPC_LOCO_DIRF, OPC_LOCO_SND, OPC_LOCO_F912,<br>OPC_EXP_CMD|
|0x04000000<br>Siehe auch Ka|Weichen-spezifische**LocoNet**-Meldungen an LAN Client weiterleiten:<br>OPC_SW_REQ, OPC_SW_REP, OPC_SW_ACK, OPC_SW_STATE<br>pitel**_9_**LocoNet.|
|**Ab Z21 FW V**<br>0x08000000|**ersion 1.22:**<br>Status-Meldungen von Gleisbesetztmeldern am LocoNet-Bus an LAN Client senden.<br>Siehe**9.5**LAN_LOCONET_DETECTOR|
|**Ab Z21 FW V**<br>0x00040000|**ersion 1.29:**<br>Änderungen bei RailCom-Daten werden automatisch gesendet.<br>Client bekommt LAN_RAILCOM_DATACHANGED, auch ohne vorher die<br>entsprechenden Lok-Adressen abonnieren zu müssen, d.h. für alle gesteuerten Loks!<br>Dieses Flag darf aufgrund des hohen Netzwerkverkehrs nur von vollwertigen<br>PC-Steuerungen verwendet werden und ist keinesfalls für mobile Handregler gedacht.<br>Broadcast Meldung der Z21 siehe**8.1**LAN_RAILCOM_DATACHANGED|



Dokumentenversion 1.13 

16/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **Ab Z21 FW Version 1.30:** 

0x00080000 Status-Meldungen von Gleisbesetztmeldern am CAN-Bus an LAN Client senden. Siehe **10.1** LAN_CAN_DETECTOR 

### **Ab Z21 FW Version 1.41:** 

0x00020000 CAN-Bus Booster Status-Meldungen an LAN Client weiterleiten. Siehe **10.2.3** LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD 

**Ab Z21 FW Version 1.43:** 0x00000010 Fastclock Modellzeit Meldungen an LAN Client senden. Siehe **12.2** LAN_FAST_CLOCK_DATA 

Antwort von Z21: keine 

**Berücksichtigen Sie bei den Einstellungen zu den Broadcast-Flags auch die Auswirkungen auf die Netzwerkauslastung. Dies gilt vor allem für die Broadcast-Flags 0x00010000, 0x00040000, 0x02000000 und 0x04000000!** Die IP-Pakete dürfen vom Router bei Überlast gelöscht werden und UDP bietet keine hierfür keine Erkennungsmechanismen! Beispielsweise bei Flag 0x00000100 - (Systemzustand) ist es überlegenswert, ob nicht 0x00000001 mit den entsprechenden _LAN_X_BC_xxx_ Broadcast-Meldungen eine sinnvollere Alternative darstellt. Denn nicht jede Anwendung muss jederzeit bis ins Detail über die aktuellsten Spannungs-, Strom- und Temperaturwerte der Zentrale informiert sein. 

### **_2.17 LAN_GET_BROADCASTFLAGS_** 

Auslesen der Broadcast-Flags in der Z21. 

|Anforderung an<br>|Z21:<br>||
|---|---|---|
|**DataLen**|**Header**|**Data**|
|0x04<br>0x00|**0x51**<br>0x00|-|
|Antwort von Z21|:||
|**DataLen**|**Header**|**Data**|
|0x08<br>0x00|**0x51**<br>0x00|Broadcast-Flags 32 Bit (little endian)|



Broadcast-Flags siehe oben. 

Dokumentenversion 1.13 

17/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.18 LAN_SYSTEMSTATE_DATACHANGED_** 

Änderung des Systemzustandes von der Z21 an den Client melden. 

Diese Meldung wird asynchron von der Z21 an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000100 

- den Systemzustand explizit angefordert hat, siehe unten _2.19_ LAN_SYSTEMSTATE_GETDATA. 

### <u>Z21 an Client:</u> 

|**DataLen**<br>**Head**|**er**<br>**Data**|||
|---|---|---|---|
|0x14<br>0x00<br>**0x84**|0x00<br>**System**|**State**(16|Bytes)|
|**SystemState**ist wie fol<br>**Byte Offset**<br>**Typ**|gt aufgebaut (die 16-bi<br>**Name**|t Werte si|nd little endian):|
|0<br>INT16|MainCurrent|mA|Strom am Hauptgleis|
|2<br>INT16|ProgCurrent|mA|Strom am Programmiergleis|
|4<br>INT16|FilteredMainCurrent|mA|geglätteter Strom am Hauptgleis|
|6<br>INT16|Temperature|°C|interne Temperatur in der Zentrale|
|8<br>UINT16|SupplyVoltage|mV|Versorgungsspannung|
|10<br>UINT16|VCCVoltage|mV|interne Spannung, identisch mit Gleisspannung|
|12<br>UINT8|CentralState|bitmask|siehe unten|
|13<br>UINT8|CentralStateEx|bitmask|siehe unten|
|14<br>UINT8|reserved|||
|15<br>UINT8|Capabilities|bitmask|siehe unten, abZ21 Version V1.42|



|Bitmasken für CentralState:|||
|---|---|---|
|`#define csEmergencyStop`|`0x01`|`// Der Nothalt ist eingeschaltet`|
|`#define csTrackVoltageOff`|`0x02`|`// Die Gleisspannung ist abgeschaltet`|
|`#define csShortCircuit`|`0x04`|`// Kurzschluss`|
|`#define csProgrammingModeActive`|`0x20`|`// Der Programmiermodus ist aktiv`|
|Bitmasken für CentralStateEx:|||
|`#define cseHighTemperature`|`0x01`|`// zu hohe Temperatur`|
|`#define csePowerLost`|`0x02`|`// zu geringe Eingangsspannung`|
|`#define cseShortCircuitExternal`|`0x04`|`// am externen Booster-Ausgang`|
|`#define cseShortCircuitInternal`|`0x08`|`// am Hauptgleis oder Programmiergleis`|
|**Ab Z21 FW Version 1.42:**|||
|`#define cseRCN213`|`0x20`|`// Weichenadressierung gem. RCN213`|
|**Ab Z21 FW Version 1.42:**|||
|Bitmasken für Capabilities:|||
|`#define capDCC`|`0x01`|`// beherrscht DCC`|
|`#define capMM`|`0x02`|`// beherrscht MM`|
|`//#define capReserved`|`0x04`|`// reserviert für zukünftige Erweiterungen`|
|`#define capRailCom`|`0x08`|`// RailCom ist aktiviert`|
|`#define capLocoCmds`|`0x10`|`// akzeptiert LAN-Befehle für Lokdecoder`|
|`#define capAccessoryCmds`|`0x20`|`// akzeptiert LAN-Befehle für Zubehördecoder`|
|`#define capDetectorCmds`|`0x40`|`// akzeptiert LAN-Befehle für Belegtmelder`|
|`#define capNeedsUnlockCode`|`0x80`|`// benötigt Freischaltcode (z21start)`|



SystemState.Capabilities verschafft dem LAN-Client einen Überblick über Feature-Umfang des Geräts. Falls SystemState.Capabilities == 0 ist, dann kann man davon ausgehen, dass es sich um eine ältere Firmwareversion handelt. Bei älteren Firmware-Versionen sollte SystemState.Capabilities nicht ausgewertet werden! 

Dokumentenversion 1.13 

18/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.19 LAN_SYSTEMSTATE_GETDATA_** 

Anfordern des aktuellen Systemzustandes. 

<u>Anforderung an Z21:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|0x04|0x00|**0x85**|0x00|-|



Antwort von Z21: 

Siehe oben _2.18_ LAN_SYSTEMSTATE_DATACHANGED 

### **_2.20 LAN_GET_HWINFO_** 

### **Ab Z21 FW Version 1.20 und SmartRail FW Version V1.13.** 

Mit diesem Kommando kann der Hardware-Typ und die Firmware-Version der Z21 ausgelesen werden. 

<u>Anforderung an Z21:</u> 

|<br>**DataLe**|<br>**n**|<br>**Header**||**Data**||
|---|---|---|---|---|---|
|0x04|0x00|**0x1A**|0x00|-||
|Antwort|von Z21|:||||
|**DataLe**|**n**|**Header**||**Data**||
|0x0C|0x00|**0x1A**|0x00|HwType 32 Bit (little endian)|FW Version32 Bit (little endian)|



### **HwType** : 

```
#define D_HWT_Z21_OLD 0x00000200 // „schwarze Z21” (Hardware-Variante ab 2012)
#define D_HWT_Z21_NEW 0x00000201 // „schwarze Z21”(Hardware-Variante ab 2013)
#define D_HWT_SMARTRAIL 0x00000202 // SmartRail (ab 2012)
#define D_HWT_z21_SMALL 0x00000203 // „weiße z21” Starterset-Variante (ab 2013)
#define D_HWT_z21_START 0x00000204 // „z21 start” Starterset-Variante (ab 2016)
#define D_HWT_SINGLE_BOOSTER 0x00000205 // 10806 „Z21 Single Booster” (zLink)
#define D_HWT_DUAL_BOOSTER  0x00000206 // 10807 „Z21 Dual Booster” (zLink)
#define D_HWT_Z21_XL 0x00000211 // 10870 „Z21 XL Series”  (ab 2020)
#define D_HWT_XL_BOOSTER 0x00000212 // 10869 „Z21 XL Booster” (ab 2021, zLink)
#define D_HWT_Z21_SWITCH_DECODER 0x00000301 // 10836 „Z21 SwitchDecoder” (zLink)
#define D_HWT_Z21_SIGNAL_DECODER 0x00000302 // 10836 „Z21 SignalDecoder” (zLink)
```

Die **FW Version** wird im BCD-Format angegeben. 

Beispiel: 

**`0x0C 0x00 0x1A 0x00 0x00 0x02 0x00 0x00 0x20 0x01 0x00 0x00`** bedeutet: „Hardware Typ **0x200,** Firmware Version **1.20** “ 

Um die Version einer älteren Firmware auszulesen, verwenden Sie alternativ den Befehl **_2.15_** LAN_X_GET_FIRMWARE_VERSION. Für ältere Firmwareversionen gilt dabei: 

- V1.10 ... Z21 (Hardware-Variante ab 2012) 

- V1.11 ... Z21 (Hardware-Variante ab 2012) 

- V1.12 ... SmartRail (ab 2012) 

Dokumentenversion 1.13 

19/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_2.21 LAN_GET_CODE_** 

Mit diesem Kommando kann der SW Feature-Umfang der Z21 geprüft und ausgelesen werden. 

Dieses Kommando ist besonders bei der Hardwarevariante „z21 start“ von Interesse, um überprüfen zu können, ob das Fahren und Schalten per LAN gesperrt oder erlaubt ist. 

|Anforderung an<br>|Z21:<br>|||
|---|---|---|---|
|**DataLen**|**Header**||**Data**|
|0x04<br>0x00|**0x18**|0x00|-|
|Antwort von Z21:||||
|**DataLen**|**Header**||**Data**|
|0x05<br>0x00|**0x18**|0x00|Code (8 Bit)|



### **Code** : 

```
#define Z21_NO_LOCK        0x00  // keine Features gesperrt
#define z21_START_LOCKED   0x01  // „z21 start”: Fahren und Schalten per LAN gesperrt
#define z21_START_UNLOCKED 0x02  // „z21 start”: alle Feature-Sperren aufgehoben
```

Dokumentenversion 1.13 

20/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **3 Einstellungen** 

Die folgenden hier beschriebenen Einstellungen werden in der Z21 persistent abgespeichert. Diese Einstellungen können vom Anwender auf die Werkseinstellung zurückgesetzt werden, indem die STOP-Taste an der Z21 gedrückt bleibt wird bis die LEDs violett blinken. 

### **_3.1 LAN_GET_LOCOMODE_** 

Lesen des Ausgabeformats für eine gegebene Lok-Adresse. 

In der Z21 kann das Ausgabeformat (DCC, MM)  pro Lok-Adresse persistent gespeichert werden. Es können maximal 256 verschiedene Lok-Adressen abgelegt werden. Jede Adresse >= 256 ist automatisch DCC. 

<u>Anforderung an Z21:</u> 

|<br>**DataLen**|<br>**Header**||**Data**||
|---|---|---|---|---|
|0x06<br>0x00|**0x60**|0x00|Lok-Adresse 16 bit (**big endian**)||
|Antwort von Z21|:||||
|**DataLen**|**Header**||**Data**||
|0x07<br>0x00|**0x60**|0x00|Lok-Adresse 16 Bit (**big endian**)|Modus 8 bit|



Lok-Adresse 2 Byte, **big endian** d.h. zuerst  high byte, gefolgt von low byte. 

Modus 0 ... DCC Format 1 ... MM Format 

### **_3.2 LAN_SET_LOCOMODE_** 

Setzen des Ausgabeformats für eine gegebene Lok-Adresse. Das Format wird persistent in der Z21 gespeichert. 

<u>Anforderung an Z21:</u> 

|**DataLen**|**Header**|**Data**||
|---|---|---|---|
|0x07<br>0x00|**0x61**<br>0x00|Lok-Adresse 16 Bit (**big endian**)|Modus 8 bit|



Antwort von Z21: keine 

Bedeutung der Werte siehe oben. 

**Anmerkung:** jede Lok-Adresse >= 256 ist und bleibt automatisch „Format DCC“. 

**Anmerkung** : die Fahrstufen (14, 28, 128) werden ebenfalls in der Zentrale persistent abgespeichert. Dies geschieht automatisch beim Fahrbefehl, siehe **_4.2_** LAN_X_SET_LOCO_DRIVE. 

Dokumentenversion 1.13 

21/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_3.3 LAN_GET_TURNOUTMODE_** 

Lesen der Einstellungen für eine gegebene Funktionsdecoder-Adresse („Funktionsdecoder“ im Sinne von „Accessory Decoder“ RP-9.2.1). 

In der Z21 kann das Ausgabeformat (DCC, MM)  pro Funktionsdecoder-Adresse persistent gespeichert werden. Es können maximal 256 verschiedene Funktionsdecoder -Adressen gespeichert werden. Jede Adresse >= 256 ist automatisch DCC. 

|Anforderung an<br>|Z21:<br>|||
|---|---|---|---|
|**DataLen**|**Header**||**Data**|
|0x06<br>0x00<br>Antwort von Z21<br>|**0x70**<br>:<br>|0x00|Funktionsdecoder-Adresse16 bit (**big endian**)<br>|
|**DataLen**|**Header**||**Data**|
|0x07<br>0x00|**0x70**|0x00|Funktionsdecoder-Adresse 16 Bit (**big endian**)<br>Modus 8 bit|
|Funktionsdecod|er-Adresse|2 B|yte,**big endian**d.h. zuerst high byte, gefolgt von low byte.|
|Modus||0 ..<br>1 ..|. DCC Format<br>. MM Format|



An der LAN-Schnittstelle und in der Z21 werden die Funktionsdecoder-Adressen ab 0 adressiert, in der Visualisierung in den Apps oder auf der multiMaus jedoch ab 1. Dies ist lediglich ist eine Entscheidung der Visualisierung. Beispiel: multiMaus Weichenadresse #3, entspricht am LAN und in der Z21 der Adresse 2. 

### **_3.4 LAN_SET_TURNOUTMODE_** 

Setzen des Ausgabeformats für eine gegebene Funktionsdecoder -Adresse. Das Format wird persistent in der Z21 gespeichert. 

|Anforderung an Z21:<br>**DataLen**<br>**Header**|**Data**||
|---|---|---|
|0x07<br>0x00<br>**0x71**<br>0x00|Funktionsdecoder-Adresse 16 Bit (**big endian**)|Modus 8 bit|
|Antwort von Z21:<br>keine|||



Bedeutung der Werte siehe oben. 

MM-Funktionsdecoder werden von Z21 Firmware ab Firmware Version 1.20 unterstützt. MM-Funktionsdecoder werden von SmartRail nicht unterstützt. 

**Anmerkung:** jede Funktionsdecoder-Adresse >= 256 ist und bleibt automatisch „Format DCC“. 

Dokumentenversion 1.13 

22/78 

06.11.2023 





<!-- Start of picture text -->
Client! -Client2<br>i} i} |<br>Actor =\ LAN_SET1BROADCAST 0oO0 00rTwv—Oa—emFLAGS 0x00000001s>ws. OS|<br>| LAN_SET_BROADCAST FLAGS oxoo00000|<br>' LAN_X_GET_LOCO_INFO<br>| 3<br>! i}| i}le LAN X_LOCO_INFO 3,v=0f0=0,... ||<br>H LAN_X_GET_LOCO_INFO3 >|<br>| I<br>|<br>| | ‘ LAN_X_LOCO_INFO|  3,v=0f0=0, ... |<br>| i} i} |<br>| i} i} |<br>||<br>|Lok #3, Fahrstufe 8 | \<br>; LAN_X_SET_LOCO_DRIVE 3,V=8<br>|| | i}<br>| le LAN X LOCO INFO 3,v=8f0=0,.. |<br>|| '| ‘ LAN_X LOCO INFO 3.v=8f0=0, .. |<br>\\\<br>|| I !<br>Lok#3, i} |<br>FO=1 SI<br>| LAN_X_SET_LOCOIFUNCTION 3, f0=1 : |<br>|<br>\<br>| ic LAN_X LOCO INFO 3y=8f0=1,... |<br>\ i} |<br>le LAN_X_LOCO_INFO 3.v=8f0=1, .. \<br>\ \<br>| \ |<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



### **_4.2 LAN_X_SET_LOCO_DRIVE_** 

Mit folgendem Kommando kann die Fahrstufe eines Lok-Decoders verändert werden. 

|Anfor<br>**DataL**|derung<br>**en**|an Z21:<br>**Heade**|**r**|**Data**||||||
|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A|0x00|**0x40**|0x00|**0xE4**|**0x1S**|**Adr_MSB**|**Adr_LSB**|**RVVVVVVV**|XOR-Byte|



Es gilt: Lok-Adresse = ( **Adr_MSB** & 0x3F) << 8 + **Adr_LSB** Bei Lok-Adressen ≥ 128 müssen die beiden höchsten Bits in DB1 auf 1 gesetzt sein: **DB1** = ( **0xC0** | **Adr_MSB** ). Bei Lokadressen < 128 sind diese beiden höchsten bits ohne Bedeutung. 

0x1 **S** Anzahl der Fahrstufen, abhängig vom eingestellten Schienenformat S=0: DCC  14 Fahrstufen bzw. MMI mit 14 Fahrstufen und F0 S=2: DCC  28 Fahrstufen bzw. MMII mit 14 realen Fahrstufen und F0-F4 S=3: DCC 128 Fahrstufen (alias „126 Fahrstufen“ ohne die Stops), bzw. MMII mit 28 realen Fahrstufen (Licht-Trit) und F0-F4 

- **RVVVVVVV** R ... Richtung: 1=vorwärts 

V ... Geschwindigkeit: abhängig von den Fahrstufen S. Codierung siehe unten. Sollte für die Lok das Format MM konfiguriert sein, erfolgt die Umrechnung der gegebenen DCC-Fahrstufe in die reale MM-Fahrstufe automatisch in der Z21. 

Die Codierung der Geschwindigkeit erfolgt ähnlich wie  in NMRA S 9.2 und S 9.2.1. „ **Stop** “ bedeutet „normaler Stop“ bzw. „Step 0“. „ **E-Stop** “ bedeutet „Nothalt“. 

### Fahrstufen -Codierung bei „DCC 14“: 

|**R000 VVVV**|**Speed**|**R000 VVVV**|**Speed**|**R000 VVVV**|**Speed**|**R000 VVVV**|**Speed**|
|---|---|---|---|---|---|---|---|
|R0000000|**Stop**|R0000100|Step 3|R0001000|Step 7|R0001100|Step 11|
|R0000001|**E-Stop**|R0000101|Step 4|R0001001|Step 8|R0001101|Step 12|
|R0000010|Step 1|R0000110|Step 5|R0001010|Step 9|R0001110|Step 13|
|R0000011|Step 2|R0000111|Step 6|R0001011|Step 10|R0001111|Step 14**max**|



Fahrstufen-Codierung bei „DCC 28“ (ähnlich „DCC 14“ mit einem Zwischenschritt im fünften Bit **V5** <u>):</u> 

|**R00V5 VVVV**|**Speed**|**R00V5 VVVV**|**Speed**|**R00V5 VVVV**|**Speed**|**R00V5 VVVV**|**Speed**|
|---|---|---|---|---|---|---|---|
|R0000000|**Stop**|R0000100|Step 5|R0001000|Step 13|R0001100|Step 21|
|R0010000|**Stop**<sup>**1**</sup>|R0010100|Step 6|R0011000|Step 14|R0011100|Step 22|
|R0000001|**E-Stop**|R0000101|Step 7|R0001001|Step 15|R0001101|Step 23|
|R0010001|**E-Stop**<sup>**1**</sup>|R0010101|Step 8|R0011001|Step 16|R0011101|Step 24|
|R0000010|Step 1|R0000110|Step 9|R0001010|Step 17|R0001110|Step 25|
|R0010010|Step 2|R0010110|Step 10|R0011010|Step 18|R0011110|Step 26|
|R0000011|Step 3|R0000111|Step 11|R0001011|Step 19|R0001111|Step 27|
|R001 0011|Step4|R001 0111|Step12|R0011011|Step20|R0011111|Step28 **max**|



Fahrstufen-Codierung bei „DCC 128“: 

|**RVVV VVVV**|**Speed**|
|---|---|
|R000 0000|**Stop**|
|R000 0001|**E-Stop**|
|R000 0010|Step 1|
|R000 0011|Step 2|
|R000 0100|Step 3|
|R000 0101|Step 4|
|…|…|
|R111 1110|Step 125|
|R111 1111|Step 126**max**|



> 1 Verwendung nicht empfohlen 

Dokumentenversion 1.13 

24/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



Antwort von Z21: 

keine Standardantwort, _4.4_ LAN_X_LOCO_INFO an Clients mit Abo. 

**Anmerkung** : eine Änderung der Anzahl der Fahrstufen (14/28/128) wird für die gegebene Lokadresse automatisch in der Zentrale persistent abgespeichert. 

### **_4.3 Funktionen für Fahrzeugdecoder_** 

Funktionsbefehle von F0 bis inklusive F12 werden am Gleis - so wie die Fahrstufe und Fahrtrichtung – regelmäßig (prioritätsgesteuert), wiederholt ausgegeben. 

Funktionsbefehle ab F13 werden dagegen nach einer Änderung drei Mal am Gleis ausgegeben, und danach aber aus Rücksicht auf die verfügbare Bandbreite am Gleis und im Sinne von RCN-212 bis zur nächsten Änderung nicht mehr regelmäßig wiederholt. 

### **4.3.1 LAN_X_SET_LOCO_FUNCTION** 

Mit folgendem Kommando kann eine Einzelfunktion eines Lok-Decoders geschaltet werden. 

|Anford<br>**DataLe**|erung an<br>**n**|Z21:<br>**Header**||**Data**||||||
|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A|0x00|**0x40**|0x00|**0xE4**|**0xF8**|**Adr_MSB **|**Adr_LSB **|**TTNN NNNN**|XOR-Byte|



Es gilt: Lok-Adresse = ( **Adr_MSB** & 0x3F) << 8 + **Adr_LSB** Bei Lok-Adressen ≥ 128 müssen die beiden höchsten Bits in DB1 auf 1 gesetzt sein: **DB1** = ( **0xC0** | **Adr_MSB** ). Bei Lokadressen < 128 sind diese beiden höchsten bits ohne Bedeutung. 

**TT** Umschalttyp: 00=aus, 01=ein, 10=umschalten,11=nicht erlaubt **NNNNNN** Funktionsindex, 0x00=F0 (Licht), 0x01=F1 usw. 

Bei Motorola MMI kann nur F0, bei MMII F0 bis F4 geschaltet werden. 

Bei DCC können hier F0 bis F28 geschaltet werden, **ab Z21 FW Version 1.42** der erweiterte Bereich von **F0 bis F31** . 

Antwort von Z21: 

keine Standardantwort, _4.4_ LAN_X_LOCO_INFO an Clients mit Abo. 

Dokumentenversion 1.13 

25/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **4.3.2 LAN_X_SET_LOCO_FUNCTION_GROUP** 

Mit folgendem Kommando kann alternativ zu den Einzelfunktionen eine ganze Funktionsgruppe eines Lok-Decoders geschaltet werden. Dabei werden bis zu 8 Funktionen mit einem einzigen Befehl geschaltet. Ab **Z21 FW Version 1.42** können DCC Funktionen bis F31 geschaltet werden, mit gewissen Einschränkungen sogar bis F68. 

Der Client sollte dabei ständig den aktuellen Zustand aller Funktionen der gesteuerten Lok mitverfolgen, damit beim Senden dieses Befehls nicht versehentlich eine Funktion gelöscht wird, welche vorher eventuell von einem anderen LAN-Client oder Handregler gesetzt worden ist. Aus diesem Grund ist dieser Befehl eher für PC-Steuerungen geeignet, weil diese ohnehin den Überblick über alle Fahrzeuge behalten sollten. 

|Anforderung an|Z21:|||||||
|---|---|---|---|---|---|---|---|
|**DataLen**|**Header**|**Data**||||||
|||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A<br>0x00|**0x40**<br>0x00|**0xE4**|**Group**|**Adr_MSB**|**Adr_LSB**|**Functions**|XOR-Byte|



Es gilt: Lok-Adresse = ( **Adr_MSB** & 0x3F) << 8 + **Adr_LSB** Bei Lok-Adressen ≥ 128 müssen die beiden höchsten Bits in DB1 auf 1 gesetzt sein: **DB1** = ( **0xC0** | **Adr_MSB** ). Bei Lokadressen < 128 sind diese beiden höchsten bits ohne Bedeutung. 

**<u>Group</u>** <u>und</u> **<u>Functions</u>** <u>sind wie folgt aufgebaut:</u> 

|**Nummer**|**Group**|<br>**Functi**|<br>**ons**|||||||**Anmerkungen**|
|---|---|---|---|---|---|---|---|---|---|---|
||**HEX**|**Bit 7**|**Bit 6**|**Bit 5**|**Bit 4**|**Bit 3**|**Bit 2**|**Bit 1**|**Bit 0**||
|1|**0x20**|0|0|0|F0|F4|F3|F2|F1|(A)|
|2|**0x21**|0|0|0|0|F8|F7|F6|F5||
|3|**0x22**|0|0|0|0|F12|F11|F10|F9||
|4|**0x23**|F20|F19|F18|F17|F16|F15|F14|F13|(B)|
|5|**0x28**|F28|F27|F26|F25|F24|F23|F22|F21|(B)|
|6|**0x29**|F36|F35|F34|F33|F32|**F31**|**F30**|**F29**|**(C)** (D) (E)|
|7|**0x2A**|F44|F43|F42|F41|F40|F39|F38|F37|(D) (E)|
|8|**0x2B**|F52|F51|F50|F49|F48|F47|F46|F45|(D) (E)|
|9|**0x50**|F60|F59|F58|F57|F56|F55|F54|F53|(D) (E)|
|10|**0x51**|F68|F67|F66|F65|F64|F63|F62|F61|(D) (E)|



### **Anmerkungen:** 

- (A) Beim Motorola MMI kann nur F0, bei MMII F0 bis maximal F4 geschaltet werden. 

- (B) DCC F13 bis F28 mit diesem Befehl erst **ab Z21 FW V1.24.** 

- (C) DCC F29 bis F31 **ab Z21 FW V1.42,** inklusive Rückmeldung an die LAN-Clients, siehe unten. 

- (D) DCC F32 bis F68 **ab Z21 FW V1.42,** es erfolgt allerdings keine Rückmeldung an die LAN-Clients, die DCC Funktionsbefehle werden nur am Gleis ausgegeben. 

- (E) Wir können nicht gewährleisten, dass die DCC-Funktionsbefehle ab F29 und höher auch tatsächlich von allen aktuell verfügbaren Decodern verstanden werden! Aktuell (2022) kennen tatsächlich nur sehr wenige DCC Decoder-Typen die Funktionsbefehle ab F29 (getestet wurden F29 bis F31 erfolgreich mit „Loksound 5“-Decoder). Andere Hersteller bieten inzwischen zwar auch schon Soundfunktionen auf F29, F30 oder F31 ab Werk an, was dann aber in der Praxis aber oft nicht mit DCC funktioniert, weil ihre Multiprotokoll-Decoder die entsprechenden neuen DCC Befehle noch gar nicht verstehen. 

Antwort von Z21: 

keine Standardantwort, für die Funktionen **F0 bis F31** erfolgt die Rückmeldung _4.4_ LAN_X_LOCO_INFO an Clients mit Abo. 

Dokumentenversion 1.13 

26/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **4.3.3 LAN_X_SET_LOCO_BINARY_STATE** 

**Ab Z21 FW Version 1.42** kann mit folgendem Kommando ein DCC „Binary State“ Kommando an einen Lok-Decoder gesendet werden. 

|Anford|erung|an Z21:||||||||
|---|---|---|---|---|---|---|---|---|---|
|**DataL**|**en**|**Header**|**Data**|||||||
||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**DB4**|**XOR-Byte**|
|0x0A|0x00|**0x40**<br>0x00|**0xE5**|**0x5F**|**AH**|**AL**|**FLLL LLLL**|**HHHH HHHH**|XOR-Byte|



Es gilt: Lok-Adresse = ( **AH** & 0x3F) << 8 + **AL** Bei Lok-Adressen ≥ 128 müssen die beiden höchsten Bits in DB1 auf 1 gesetzt sein: **DB1** = ( **0xC0** | **AH** ). Bei Lokadressen < 128 sind diese beiden höchsten bits ohne Bedeutung. 

**F** Das oberste Bit **F** legt fest, ob der Binärzustand eingeschaltet oder ausgeschaltet ist. **LLLLLLL** Die niederwertigen **sieben** (!) Bits der Binärzustandsadresse. **HHHHHHHH** Die die höherwertigen acht Bits der Binärzustandsadresse. 

Es gilt: die 15-Bit Binärzustandsadresse = ( **HHHHHHHH** << **7** ) + ( **LLLLLLL** & 0x7F) 

Erlaubt sind die Binärzustandsadressen von **29 bis 32767** . Es dürfen für allgemeine Schaltfunktionen nur die Binärzustandsadressen ≥ 29 verwendet werden. Die Binärzustandsadressen von 1 bis 28 sind für besondere Anwendungen reserviert. Die Binärzustandsadresse 0 ist als Broadcast reserviert. 

Binärzustandsadressen < 128 (d.h. falls **HHHHHHHH** == 0) werden **automatisch** gemäß RCN-212 als DCC „Binärzustandssteuerungsbefehl **kurze Form** “ am Gleis ausgegeben, ab ≥ 128 als DCC „Binärzustandssteuerungsbefehl **lange Form** “. 

DCC Binärzustandssteuerungsbefehle werden drei Mal am Gleis ausgegeben, und danach gemäß RCN212 nicht mehr regelmäßig wiederholt. 

Es erfolgt keine Antwort an den Aufrufer und auch keine Benachrichtigung an andere Clients. 

Antwort von Z21: keine. 

Dokumentenversion 1.13 

27/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_4.4 LAN_X_LOCO_INFO_** 

Diese Meldung wird von der Z21 an die Clients als Antwort auf das Kommando 

- _4.1_ LAN_X_GET_LOCO_INFO gesendet. Sie wird aber auch ungefragt an Clients gesendet, wenn 

   - der Lok-Status durch einen der Clients oder Handregler verändert worden ist 

   - und der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

   - und der betreffende Client die Lok-Adresse mit _4.1_ LAN_X_GET_LOCO_INFO abonniert hat 

<u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**||**Data**||||
|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**...**<br>**...**<br>**...**<br>**...**<br>**...**<br>**...**<br>**...**<br>**DB****_n_**|**XOR-Byte**|
|7 +**_n_**|0x00|**0x40**|0x00|0xEF|**Lok-In**|**formation**|XOR-Byte|



Die aktuelle Paketlänge kann abhängig von den tatsächlich gesendeten Daten variieren mit **_7_**  **_n_**  **_14_** . **Ab Z21 FW Version 1.42** ist DataLen ≥ 15 ( **n ≥ 8** ), zur Übertragung des Status von F29, F30 und F31! 

<u>Die Daten für</u> **<u>Lok-Information</u>** <u>sind folgendermaßen aufgebaut:</u> 

|**Position**|**Daten**|<br>**Bedeutung**|
|---|---|---|
|DB0|**Adr_MSB**|Die beiden höchsten Bits in Adr_MSB sind zu ignorieren.|
|DB1|**Adr_LSB**|Lok-Adresse=(**Adr_MSB**& 0x3F) << 8 +**Adr_LSB**|
|DB2|000**MBKKK**|**M**=1 …**Ab Z21 FW Version 1.43**Kennung für MM Lok|
|||**B**=1  ... die Lok wird von einem anderen X-BUS Handregler<br>gesteuert („_besetzt_“)<br>**KKK**... Fahrstufeninformation: 0=14, 2=28, 4=128<br>0: DCC  14 Fahrstufen bzw. MMI mit 14 Fahrstufen und F0<br>2: DCC  28 Fahrstufen bzw. MMII mit 14 realen Fahrstufen und F0-F4<br>**4**: DCC 128 Fahrstufen<br>bzw. MMII mit 28 realen Fahrstufen (Licht-Trit) und F0-F4|
|DB3|**RVVVVVVV**|**R**... Richtung: 1=vorwärts<br>**V**... Geschwindigkeit.<br>Codierung abhängig von der Fahrstufeninformation KKK.<br>Siehe auch oben_4.2_LAN_X_SET_LOCO_DRIVE.<br>Sollte für die Lok das Format MM konfiguriert sein, dann ist die Umrechnung<br>der realen MM-Fahrstufe in die vorliegende DCC-Fahrstufe bereits in der<br>Z21 erfolgt.|
|DB4|0**DSLFGHJ**|**D**... Doppeltraktion: 1=Lok in Doppeltraktion enthalten.<br>**S**... Smartsearch<br>**L**... F0 (Licht)<br>**F**... F4<br>**G**... F3<br>**H**... F2<br>**J**... F1|
|DB5|F5-F12|Funktion F5 ist bit0 (LSB)|
|DB6|F13-F20|Funktion F13 ist bit0 (LSB)|
|DB7|F21-F28|Funktion F21 ist bit0 (LSB)|
|DB8<br>DB**_n_**|**F29-F31**|**Ab Z21 FW Version 1.42**und falls DataLen≥15; Funktion F29 ist bit0 (LSB)<br>optional, für zukünftige Erweiterungen|



Dokumentenversion 1.13 

28/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_4.5 LAN_X_SET_LOCO_E_STOP_** 

**Ab Z21 FW Version 1.43** kann mit folgendem Kommando eine Lok angehalten werden. Bei einer DCC Lok wird dann am Gleis beim DCC Geschwindigkeitsbefehl die Fahrstufe „ **E-STOP** “ („Nothalt“ lt. RCN212) ausgegeben, d.h. der Decoder soll das Fahrzeug so schnell wie möglich anhalten. Bei einer MM Lok wird die Fahrstufe 0 („Stop“) ausgegeben. 

|Anfor|derung|an Z21:|||||
|---|---|---|---|---|---|---|
|**DataL**|**en**|**Header**|**Data**||||
||||**X-Header**|**DB0**|**DB2**|**XOR-Byte**|
|0x08|0x00|**0x40**<br>0x00|**0x92**|**Adr_MSB**|**Adr_LSB**|XOR-Byte|



Es gilt: Lok-Adresse = ( **Adr_MSB** & 0x3F) << 8 + **Adr_LSB** Bei Lok-Adressen ≥ 128 müssen die beiden höchsten Bits in DB1 auf 1 gesetzt sein: **DB1** = ( **0xC0** | **Adr_MSB** ). Bei Lokadressen < 128 sind diese beiden höchsten bits ohne Bedeutung. 

Antwort von Z21: keine Standardantwort, _4.4_ LAN_X_LOCO_INFO an Clients mit Abo. 

### **_4.6 LAN_X_PURGE_LOCO_** 

**Ab Z21 FW Version 1.43** kann mit folgendem Kommando eine Lok wieder aus der Z21 herausgenommen werden. Damit wird auch die Ausgabe der Fahrbefehle für diese Lok auf dem Gleis beendet. Sie beginnt erst wieder, sobald ein neuer Fahr- oder Funktionsbefehl an dieselbe Lokadresse gesendet wird. 

Auf diese Weise ist es z.B. für eine PC-Steuerung möglich, die Anzahl der Loks im System und damit auch den Datendurchsatz am Gleis zu beeinflussen. 

|Anforderung an|Z21:|||||||
|---|---|---|---|---|---|---|---|
|**DataLen**|**Header**||**Data**|||||
||||**X-Header**|**DB0**|**DB1**|**DB2**|**XOR-Byte**|
|0x09<br>0x00|**0x40**|0x00|**0xE3**|**0x44**|**Adr_MSB**|**Adr_LSB**|XOR-Byte|



Es gilt: Lok-Adresse = ( **Adr_MSB** & 0x3F) << 8 + **Adr_LSB** Bei Lok-Adressen ≥ 128 müssen die beiden höchsten Bits in DB1 auf 1 gesetzt sein: **DB1** = ( **0xC0** | **Adr_MSB** ). Bei Lokadressen < 128 sind diese beiden höchsten bits ohne Bedeutung. 

Es erfolgt keine Antwort an den Aufrufer und auch keine Benachrichtigung an andere Clients. 

Antwort von Z21: keine Standardantwort. 

Dokumentenversion 1.13 

29/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **5 Schalten** 

In diesem Kapitel werden Meldungen behandelt, die zum Schalten von Funktionsdecodern im Sinne von „Accessory Decoder“ RP-9.2.1(d.h. Weichendecoder, ...) benötigt werden. 

Die Visualisierung der Weichennummer an der Benutzeroberfläche ist bei vielen DCC-Systemen unterschiedlich gelöst und kann von der tatsächlich am Gleis verwendeten Accessorydecoder-Adresse und  Port deutlich abweichen. Gemäß DCC gibt es pro Accessorydecoder-Adresse vier Ports mit  je zwei Ausgängen. Pro Port kann eine Weiche angeschlossen werden. Üblicherweise wird zur Visualisierung der Weichennummer eine von folgenden Möglichkeiten verwendet: 

1. Nummerierung ab 1 mit DCC-Adresse bei 1 beginnend mit je 4 Ports (ESU, Uhlenbrock, …) Weiche #1: DCC-Addr=1 Port=0; Weiche #5: DCC-Addr=2 Port=0; Weiche #6: DCC-Addr=2 Port=1 

2. Nummerierung ab 1 mit DCC-Adresse bei 0 beginnend mit je 4 Ports ( **Roco** , Lenz) Weiche #1: DCC-Addr=0 Port=0; Weiche #5: DCC-Addr=1 Port=0; Weiche #6: DCC-Addr=1 Port=1 

3. Virtuelle Weichennummer mit frei konfigurierbarer DCC-Adresse und Port (Twin-Center) 

4. Darstellung DCC-Adresse / Port (Zimo) 

Keine dieser Visualisierungsmöglichkeiten kann als „falsch“ bezeichnet werden. Für den Anwender ist es allerdings gewöhnungsbedürftig, dass ein und dieselbe Weiche bei einer ESU Zentrale unter Nummer 1 gesteuert wird, während sie auf der Roco multiMaus mit Z21 unter der Nummer 5 geschaltet wird („Verschiebung um 4“). 

Um in Ihrer Applikation die Visualisierung Ihrer Wahl implementieren zu können, hilft es zu wissen, wie die Z21 die Input-Parameter für die Schaltbefehle ( **FAdr_MSB** , **FAdr_LSB** , **A** , **P** , siehe unten) in den entsprechenden DCC Accessory Befehl umsetzt: 

DCC Basic Accessory Decoder Packet Format: {preamble} 0 10AAAAAA 0 1aaaCDDd 0 EEEEEEEE 1 

UINT16 _FAdr_ = ( **FAdr_MSB** << 8) + **FAdr_LSB;** UINT16 _Dcc_Addr_ = _FAdr_ >> 2; 

<u>aaaAAAAAA = (~</u> _Dcc_Addr_ & 0x1C0) | ( _Dcc_Addr_ & 0x003F); // DCC Adresse C = **A** ; // Ausgang aktivieren oder deaktivieren DD = _FAdr_ & 0x03; // Port 

<u>d =</u> **P** ; // Weiche nach links oder nach rechts 

Beispiel: FAdr=0 ergibt DCC-Addr=0 Port=0; FAdr=3 ergibt DCC-Addr=0 Port=3; FAdr=4 ergibt DCC-Addr=1 Port=0; usw 

Bei MM Format gilt dagegen: FAdr beginnt mit 0, d.h. FAdr=0: MM-Addr=1; FAdr=1: MM-Addr=2; … 

Ein Client kann Funktions-Infos abonnieren, um über Änderungen an Funktionsdecodern, welche auch durch andere Clients oder Handregler verursacht werden, automatisch informiert zu werden. Dazu muss für den Client der entsprechende Broadcast aktiviert sein, siehe **_2.16_** _LAN_SET_BROADCASTFLAGS,_ Flag 0x00000001. 

Die tatsächliche Stellung der Weiche hängt übrigens von der Verkabelung und eventuell auch von der Konfiguration in der Applikation des Clients ab. Davon kann die Zentrale nichts wissen, weshalb in der folgenden Beschreibung auf die Bezeichnungen „ _gerade_ “ und „ _abzweigend_ “ bewusst verzichtet wird. 

Dokumentenversion 1.13 

30/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_5.1 LAN_X_GET_TURNOUT_INFO_** 

Mit folgendem Kommando kann der Status einer Weiche (bzw. Schaltfunktion) angefordert werden. 

|Anforde<br>**DataLe**|rung an Z<br>**n**|21:<br>**Header**|**Data**||||
|---|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**DB1**|**XOR-Byte**|
|0x08|0x00|**0x40**<br>0x00|**0x43**|**FAdr_MSB**|**FAdr_LSB**|XOR-Byte|



Es gilt: Funktions-Adresse = ( **FAdr_MSB** << 8) + **FAdr_LSB** 

Antwort von Z21: siehe _5.3_ LAN_X_TURNOUT_INFO 

### **_5.2 LAN_X_SET_TURNOUT_** 

Mit folgendem Kommando kann eine Weiche geschaltet werden. 

|Anford<br>**DataLe**|erung an<br>**n**|Z21:<br>**Header**||**Data**|||||
|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**XOR-Byte**|
|0x09|0x00|**0x40**|0x00|**0x53**|**FAdr_MSB **|**FAdr_LSB**|10**Q**0**A**00**P**|XOR-Byte|



Es gilt: Funktions-Adresse = ( **FAdr_MSB** << 8) + **FAdr_LSB** 

1000 **A** 00 **P A** =0 ... Weichenausgang deaktivieren 

**A** =1 ... Weichenausgang aktivieren 

**P** =0 ... Ausgang 1 der Weiche wählen **P** =1 ... Ausgang 2 der Weiche wählen 

**Q** =0 … Kommando sofort ausführen 

**Q** =1 … **ab Z21 FW V1.24** : Weichenbefehl in der Z21 in die Queue einfügen und zum nächstmöglichen Zeitpunkt am Gleis ausgeben. 

Antwort von Z21: 

keine Standardantwort , _5.3_ LAN_X_TURNOUT_INFO an Clients mit Abo. 

**Ab Z21 FW V1.24** wurde das Q-Flag („Queue“) eingeführt. 

### **5.2.1 LAN_X_SET_TURNOUT mit Q=0** 

Wenn **Q=0** ist, dann verhält sich die Z21 kompatibel zu den bisherigen Versionen: der Weichenstellbefehl wird sofort auf das Gleis ausgegeben, indem er in die laufenden Fahrbefehle gemischt wird **. Das Activate (A=1) wird solange ausgegeben, bis vom LAN-Client das entsprechende Deactivate geschickt wird. Es darf zu einem Zeitpunkt nur ein Weichenstellstellbefehl aktiv sein.** Dieses Verhalten entspricht z.B. dem Drücken und Loslassen der multiMaus-Tasten. 

Beachten Sie, dass bei Q=0 unbedingt die korrekte Reihenfolge der Schaltbefehle (d.h. Activate gefolgt von Deactivate) eingehalten werden muss. Ansonsten kann es je nach verwendetem Weichendecoder zu undefinierten Endstellungen kommen. 

**Die korrekte Serialisierung und das Timing der Schaltdauer liegen in der Verantwortung des LANClients!** 

Dokumentenversion 1.13 

31/78 

06.11.2023 



DCC preamble=16 LOCO address=3 22128=0 find Speed=Stop DCC preamble=16 LOCO address=3 FG (0-4) F=Loooo DCC preamble=16 LOCO address=3 FG? (5-8) F=o7o0 DCC preamble=16 ACESSOR' raw data 44=1 OD=5 C=1 . "Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 22128=0 find Speed=Stop DCC preamble=16 ACESSOR' raw data 44=1 OD=5 C=1. "Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG (0-4) F=Loooo DCC preamble=16 ACESSOR’Y raw data A4=1 OD=5 C=1 . “Roco_lenz f=7 outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG? [6-8] F=o7o0 DCC preamble=16 ACESSOR' raw data 44=1 OD=5 C=1. "Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 s3128=0 fwd Speed=Stop DCC preamble=16 ACESSOR’Y raw data A4=1 OD=5 C=1 . “Roco_lenz f=7 outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG (0-4) F=Loooo DCC preamble=16 ACESSOR' raw data 44=1 OD=5 C=1. "Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG2 [5-8] F=o7o00 

DCC preamble=16 ACESSOR’Y’ raw data 44=7 OD=5 C=. “Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 3126-0 find Speed=Stop DCC preamble=16 ACESSORY raw data 44=7 OD=5 C21. "Rooo_lenz f=? outs4& ACTIVE" DCC preamble=16 LOCO address=3 FG [0-4] F=Loooo DCC preamble=16 ACESSOR’Y raw data 44=7 OD=6 C=1 . “Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG? (5-8) F=o7oo DCC preamble=16 ACESSORY raw data 44=7 OD=5 C21. "Rooo_lenz f=? outs4& ACTIVE" DCC preamble=16 LOCO address=3 s3128=0 fwd Speed=Stop DCC preamble=16 ACESSOR’Y raw data 44=7 OD=6 C=1 . “Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG (0-4) F=Loooo DCC preamble=16 ACESSORY raw data 44=7 OD=5 C21. "Rooo_lenz f=? outs4& ACTIVE" DCC preamble=16 LOCO address=3 Fa? [5-8] F=o7o0 DCC preamble=16 ACESSOR’Y raw data 44=1 DD=6 C=1 . “Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 2312820 fd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44=1 OD=5 C=1 . "Roco_lenz f=? outs4 ACTIVE" DCC preamble=16 LOCO address=3 FG1 [0-4] F=Loooo DCC preamble=16 ACESSORY raw data 44=7 OD=8 C0. "Roco_lenz f=? outs4 INACTIVE" DCC preamble=16 LOCO address=3 FG? (5-8) F=o7o0 DCC preamble=16 ACESSOR' raw data 44=1 OD=5 C=O, "Roco_lenz f=? outse4 INACTIVE" DCC preamble=16 LOCO address=3 2¢128=0 find Speed=Stop DCC preamble=16 ACESSORY raw data 44=7 OD=8 C0. "Roco_lenz f=? outs4 INACTIVE" DCC preamble=16 LOCO address=3 FG (0-4) F=Loooo DCC preamble=16 ACESSOR' raw data 44=1 OD=5 C=O, "Roco_lenz f=? outse4 INACTIVE" DCC preamble=16 LOCO address=3 FG? [6-8] F=o7o0 DCC preamble=16 LOCO address=3 3128-0 find Speed=Stop DCC preamble=16 LOCO address=3 FG (0-4) F=Loooo 



DCC preamble=16 LOCO address=3 3212820 fivd Speed=Stop DCC preamble=16 LOCO address=3 212620 fd Speed=Stop DCC preamble=16 LOCO address=3 21 28=0 fd Speed=Stop 

DCC preamble=16 ACESSOR'Y raw data 44=6 D021 C=1. "Roco_lenz f=25 outs4 ACTIVE DCC preamble=16 LOCO address=3 s8128=0 fiavd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44=6 D021 C=1. "Roco_lenz f=25 outs4 ACTIVE DCC preamble=16 LOCO address=3 212820 fivd Speed=Stop DCC preamble=16 ACESSORY raw data 44=6 DD=1 C=1. “Roco_lenz f=25 outs4 ACTIVE" DCC preamble=16 LOCO address=3 212620 fd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44-6 DD=1 C=1 . "'Roco_lenz f=25 outs4 ACTIVE” DCC preamble=16 LOCO address=3 3212050 fd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44=1 DD=1 C=1 . Roco_lenz f=5 outs4 ACTIVE" DCC preamble=16 LOCO address=3 3212820 fivd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44=1 DO=1 C=1 . 'Roco_lenz f=5 outs4& ACTIVE" DCC preamble=16 LOCO address=3 3212820 fivd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44=1 DO=1 C=1 . 'Roco_lenz f=5 outs4& ACTIVE" DCC preamble=16 LOCO address=3 21 28=0 fd Speed=Stop 

DCC preamble=16 ACESSOR'Y raw data 44=1 D017 C=1."Roco_lenz f=5 outs4 ACTIVE" DCC preamble=16 LOCO address=3 212820 fivd Speed=Stop DCC preamble=16 LOCO address=3 3212820 fivd Speed=Stop DCC preamble=16 LOCO address=3 212620 fd Speed=Stop DCC preamble=16 LOCO address=3 21 28=0 fd Speed=Stop DCC preamble=16 LOCO address=3 3212050 fd Speed=Stop DCC preamble=16 LOCO address=3 212820 fivd Speed=Stop DCC preamble=16 LOCO address=3 3212050 fd Speed=Stop 

DCC preamble=16 ACESSOR'Y raw data 44=6 OD=1 C=0."Roco_lenz f=25 outs4 INACTIVE" DCC preamble=16 LOCO address=3 3212820 fivd Speed=Stop DCC preamble=16 ACESSOR'Y raw data 44-6 DD=1 C=O. "Roco_leng f=25 outs4 INACTIVE" DCC preamble=16 LOCO address=3 21 28=0 fd Speed=Stop DCC preamble=16 ACESSORY raw data A4=6 DD=1 CSO. "Roco_lenz f=25 outs4 INACTIVE" DCC preamble=16 LOCO address=3 212820 fivd Speed=Stop DCC preamble=16 ACESSORY raw data 44=6 DD=1 C0. "Roco_lenz f=25 outs4 INACTIVE" DCC preamble=16 LOCO address=3 212620 fd Speed=Stop DCC preamble=16 LOCO address=3 3212850 fivd Speed=Stop DCC preamble=16 LOCO address=3 212620 fd Speed=Stop 





<!-- Start of picture text -->
Client! Client3<br>\\|<br>\\ |<br>Actor||LAN_SET. BRDADCAST.|FLAGS 0x00000001 >|<br>|| LAN SET BROADCAST FLAGS 0x00000001 |<br>\ ||<br>|\\|<br>|| | \<br>||\|<br>|\\\<br>|LAN_X_ GET TURNOUT INFO4 > I<br>||||<br><LAN_X_TURNOUT_INFO 4,0x02 |<br>\\\\<br>|\ \ \<br>|\\|<br>||\<br>! | \! |<br>|||<br>\| Weiche #5, Ausgang|  2 schalten : | |<br>| | LAN_X_SET_TURNOUT 4,0x89 |<br>\ (Ausgang 2 aktivieren) |<br>\| \| LAN_X!TURNOUT\ INFO 4,0x02 \|<br>\ i< |<br>\| \| \} LAN_X_TURNOUT_INFO 4,0x02 ||<br>\ \ l< 1<br>\ \ \ \<br>| | LAN_X_SET_TURNOUT 4,0x81 |<br>\ (Ausgang 2 deaktivieren)<br>|1 |i ! |1<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



### **_5.4 LAN_X_SET_EXT_ACCESSORY_** 

**Ab Z21 FW V1.40** kann mit folgendem Kommando ein DCC Befehl im „erweiterten Zubehördecoder Paketformat“ (DCCext) an einen Erweiterten Zubehördecoder gesendet werden. Damit ist es möglich, Schaltzeiten für Weichen oder komplexere Signalbegriffe mit nur einem Kommando zu versenden. Siehe RCN-213 (Abschnitt 2.3). 

|Anfor|derung|an Z21:||||||||
|---|---|---|---|---|---|---|---|---|---|
|**DataL**|**en**|**Heade**|**r**|**Data**||||||
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A|0x00|**0x40**|0x00|**0x54**|**Adr_MSB**|**Adr_LSB**|DDDDDDDD|0x00|XOR-Byte|



Es gilt: **RawAddress** = ( **Adr_MSB** << 8) + **Adr_LSB** 

**RawAddress** Die RawAddress für den ersten erweiterten Zubehördecoder ist gemäß RCN-213 die Adresse 4. Diese Adresse wird in Anwenderdialogen als „Adresse 1“ dargestellt. Die Adressierung richtet sich strikt nach RCN-213, d.h. es gibt hier _keine_ abweichende Adressverschiebung mehr. 

**DDDDDDDD** Über die Bits 0 bis 7 in DB2 werden die 256 möglichen Zustände übertragen. Der Inhalt wird am Gleis im **_Erweiterten Zubehördecoder Paketformat_** gemäß RCN-213 an den Decoder übertragen. 

**Hinweis** : 

Der **10836 Z21 switch DECODER** interpretiert DDDDDDDD wie ein „einfacher Schaltdecoder mit Empfang der Schaltzeit“ als **RZZZZZZZ** . Dabei gilt: 

• **ZZZZZZZ** legt die Einschaltzeit mit einer Auflösung von **100 ms** fest. `o` Der Wert 0 bedeutet, dass der Ausgang ausgeschaltet wird. `o` Der Wert 127 bedeutet, dass der Ausgang dauerhaft, d.h. bis zum nächsten Befehl an diese Adresse, eingeschaltet wird. • Bit 7 **R** wird benutzt, um den Ausgang innerhalb des Paares auszuwählen: `o` R=1 bedeutet „grün“ (gerade). `o` R=0 bedeutet „rot“ (abzweigend). 

Der **10837 Z21 signal DECODER** interpretiert DDDDDDDD dagegen als einen von 256 theoretisch möglichen Signalbegriffen. Der tatsächlich verfügbare Wertebereich hängt stark vom im Signal-Decoder eingestellten Signaltyp ab. Mögliche Werte sind zum Beispiel: • 0 ... absoluter Haltebegriff • 4 ... Fahrt mit Geschwindigkeitsbegrenzung 40 km/h • 16 ... freie Fahrt • 65 (0x41) ... Rangieren erlaubt • 66 (0x42) ... Dunkelschaltung (z.B. Lichtvorsignale) • 69 (0x45) ... Ersatzsignal (erlaubt die Vorbeifahrt) Den konkreten Wert zum gewünschten Signalbegriff für ein gegebenes Signals finden Sie für den Z21 signal DECODER unter https://www.z21.eu/de/produkte/z21-signal-decoder/signaltypen jeweils unter „DCCext“. 

Antwort von Z21: 

keine Standardantwort, oder _5.6 LAN_X_EXT_ACCESSORY_INFO_ an Clients mit Abo. 

Beispiel: 

```
0x0A 0x00 0x40 0x00 0x54 0x00 0x040x05 0x00 0x55
```

bedeutet „Sende an Decoder mit RawAddress=4 (diese Adresse wird in Anwenderdialogen als Adresse 1 dargestellt!) den Wert DDDDDDDD=5.“ 

Ist der Empfänger ein 10836 Z21 switch DECODER, dann wird dadurch der Ausgang 1 „rot“ (Klemme 1A) eingeschaltet und nach 5*100ms automatisch wieder ausgeschaltet. 

Mit diesem Kommando ist es auch möglich, den „Notaus-Befehl für Erweiterte Zubehördecoder“ gemäß RCN-213 (Abschnitt 2.4) zu versenden. Das entspricht dem Wert 0 („Halt bei Lichtsignalen“) für die RawAddress=2047: 

```
0x0A 0x00 0x40 0x00 0x54 0x07 0xFF0x00 0x00 0xAC
```

Dokumentenversion 1.13 

35/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_5.5 LAN_X_GET_EXT_ACCESSORY_INFO_** 

**Ab Z21 FW V1.40** kann mit folgendem Kommando der letzte an einen **Erweiterten Zubehördecoder** übertragene Befehl abgefragt werden. 

<u>Anforderung an Z21:</u> 

|**DataLe**|**n**|**Header**||**Data**|||||
|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**XOR-Byte**|
|0x09|0x00|**0x40**|0x00|**0x44**|**Adr_MSB**|**Adr_LSB**|0x00|XOR-Byte|



### Es gilt: **RawAddress** = ( **Adr_MSB** << 8) + **Adr_LSB** 

**RawAddress** Die Adresse des Zubehördecoders gemäß RCN-213. Siehe Abschnitt _5.4_ LAN_X_SET_EXT_ACCESSORY. 

**DB2** Reserviert für zukünftige Erweiterungen, sollte bis auf weiteres mit 0 initialisiert bleiben. 

Antwort von Z21: siehe _5.6_ LAN_X_EXT_ACCESSORY_INFO 

### **_5.6 LAN_X_EXT_ACCESSORY_INFO_** 

Diese Meldung wird von der Z21 an die Clients als Antwort auf das Kommando _5.5 LAN_X_GET_EXT_ACCESSORY_INFO_ gesendet. Sie wird aber auch ungefragt an Clients gesendet, wenn 

- irgendjemand anderer ein Kommando an einen Erweiterten Zubehördecoder sendet 

- und der betreffende Client den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000001 

<u>Z21 an Client:</u> 

|**DataL**|**en**|**Heade**|**r**|**Data**||||||
|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A|0x00|**0x40**|0x00|**0x44**|**Adr_MSB**|**Adr_LSB**|**DDDDDDDD**|**Status**|XOR-Byte|



### Es gilt: **RawAddress** = ( **Adr_MSB** << 8) + **Adr_LSB** 

**RawAddress** Die Adresse des Zubehördecoders gemäß RCN-213. Siehe Abschnitt _5.4_ LAN_X_SET_EXT_ACCESSORY. 

**DDDDDDDD** Bis zu 256 mögliche Zustände, codiert im **_Erweiterten Zubehördecoder Paketformat_** gemäß RCN-213. Siehe Abschnitt _5.4_ LAN_X_SET_EXT_ACCESSORY. 

**Status** 0x00 … Data Valid 0xFF … Data Unknown 

Dokumentenversion 1.13 

36/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **6 Decoder CV Lesen und Schreiben** 

In diesem Kapitel werden Meldungen behandelt, die zum Lesen und Schreiben von Decoder-CVs (Configuration Variable, RP-9.2.2, RP-9.2.3) benötig werden. 

Ob der Zugriff am Decoder bit- oder byteweise geschieht, hängt von den Einstellungen in der Z21 ab. 

### **_6.1 LAN_X_CV_READ_** 

Mit folgendem Kommando kann eine CV im Direct-Mode ausgelesen werden 

|Anforderung an|Z21:||||||
|---|---|---|---|---|---|---|
|**DataLen**|**Header**||**Data**||||
||||**X-Header**|**DB0**|**DB1**|**DB2**<br>**XOR-Byte**|
|0x09<br>0x00|**0x40**|0x00|**0x23**|**0x11**|**CVAdr_MSB**|**CVAdr_LSB**XOR-Byte|



Es gilt: CV-Adresse = ( **CVAdr_MSB** << 8) + **CVAdr_LSB** , sowie 0=CV1., 1=CV2, 255=CV256, usw. 

Antwort von Z21: 

_2.9_ LAN_X_BC_PROGRAMMING_MODE an Clients mit Abo, sowie das Ergebnis _6.3_ LAN_X_CV_NACK_SC _, 6.4_ LAN_X_CV_NACK oder _6.5_ LAN_X_CV_RESULT _._ 

### **_6.2 LAN_X_CV_WRITE_** 

Mit folgendem Kommando kann eine CV im Direct-Mode überschrieben werden. 

<u>Anforderung an Z21:</u> 

|**DataL**|**en**|**Heade**|**r**|**Data**||||||
|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A|0x00|**0x40**|0x00|**0x24**|**0x12**|**CVAdr_MSB**|**CVAdr_LSB**|**Value**|XOR-Byte|



Es gilt: CV-Adresse = ( **CVAdr_MSB** << 8) + **CVAdr_LSB** , sowie 0=CV1., 1=CV2, 255=CV256, usw. 

Antwort von Z21: 

_2.9_ LAN_X_BC_PROGRAMMING_MODE an Clients mit Abo, sowie das Ergebnis _6.3_ LAN_X_CV_NACK_SC _, 6.4_ LAN_X_CV_NACK oder _6.5_ LAN_X_CV_RESULT _._ 

### **_6.3 LAN_X_CV_NACK_SC_** 

Wenn die Programmierung aufgrund eines Kurzschlusses am Gleis fehlerhaft war, wird diese Meldung automatisch an den Client geschickt, der die Programmierung durch _6.1_ LAN_X_CV_READ oder _6.2_ LAN_X_CV_WRITE veranlasst hat. 

<u>Z21 an Client:</u> 

|**DataLe**|**n**|**Header**|**Data**|||
|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**XOR-Byte**|
|0x07|0x00|**0x40**<br>0x00|**0x61**|**0x12**|0x73|



Dokumentenversion 1.13 

37/78 

06.11.2023 





<!-- Start of picture text -->
Client “Client3<br>|||<br>|| |<br>Actor||LAN SETI|BROADCAST FLAGS ox00000001 SJ|<br>!|| | LAN SET BROADCAST FLAGS oxoog00001 —|<br>| | || |<br>I | | I<br>I| I<br>CV#29 lesen<br>I || 5 I<br>\ | | LAN < CV_READ 28 \<br>LAN ¥ BC PROGRAMMING MODE<br>LAN X BC PROGRAMMING MODE<br>"Pragrammier-SSs<br>| modus"<br>|<br>|<br>|<br>|<br>|<br>|<br>|<br>|<br>| "CVEE29: 6" LAN * CW_RESULT 28,6<br>| AN |x BC TRACKLAN x SETPOWERTRACKON POWER ON ||<br>|_| LAN x BC TRACK POWER ON |<br>|<br>; |<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



### **_6.6 LAN_X_CV_POM_WRITE_BYTE_** 

Mit folgendem Kommando kann eine CV eines Lokdecoders (Multi Function Digital Decoders gemäß NMRA S-9.2.1 Abschnitt C; Configuration Variable Access Instruction - Long Form) auf dem Hauptgleis geschrieben werden (POM „Programming on the Main“). Das geschieht im normalen Betriebsmodus, d.h. die Gleisspannung muss eingeschaltet sein, der normale Programmiermodus ist nicht aktiviert. Es gibt keine Rückmeldung. 

<u>Anforderung an Z21:</u> 

|<br>**DataLen**|<br>**Header**<br>**Data**|||
|---|---|---|---|
|<br>|**X-Header**<br>**DB0**<br>**DB1**<br>**DB2**<br>**DB3**<br>**DB4**|**DB5**|**XOR-Byte**|
|0x0C<br>0x|00<br>**0x40**<br>0x00<br>**0xE6**<br>**0x30**<br>**POM-Parameter**||XOR-Byte|
|Die Daten<br>**Position**|für**POM-Parameter**sind folgendermaßen aufgebaut:<br>**Daten**<br>**Bedeutung**|||
|DB1|**Adr_MSB**|||
|DB2|**Adr_LSB**<br>Lok-Adresse=(**Adr_MSB**& 0x3F) << 8 +**Adr_LSB**|||
|DB3|**111011MM**<br>**Option**...**0xEC**<br>**MM**... CVAdr_MSB|||
|DB4|**CVAdr_LSB**<br>CV-Adresse = (**MM**<< 8) +**CVAdr_LSB**<br>(0=CV1., 1=CV2, 255=CV256, usw.)|||
|DB5|**Value**<br>neuer CV-Wert|||



Antwort von Z21: keine 

### **_6.7 LAN_X_CV_POM_WRITE_BIT_** 

Mit folgendem Kommando kann ein Bit einer CV eines Lokdecoders (Multi Function Digital Decoders gemäß NMRA S-9.2.1 Abschnitt C; Configuration Variable Access Instruction - Long Form) auf dem Hauptgleis geschrieben werden (POM). Das geschieht im normalen Betriebsmodus, d.h. die Gleisspannung muss eingeschaltet sein, der normale Programmiermodus ist nicht aktiviert. Es gibt keine Rückmeldung. 

<u>Anforderung an Z21:</u> 

|<br>**DataLen**|<br>**Header**<br>**Data**<br> <br> <br> <br> <br> <br>|||
|---|---|---|---|
||**X-Header**<br>**DB0**<br>**DB1**<br>**DB2**<br>**DB3**<br>**DB4**|**DB5**|**XOR-Byte**|
|0x0C<br>0x|00<br>**0x40**<br>0x00<br>**0xE6**<br>**0x30**<br>**POM-Parameter**||XOR-Byte|
|Die Daten<br>|für**POM-Parameter**sind folgendermaßen aufgebaut:<br> <br>|||
|**Position**|**Daten**<br>**Bedeutung**|||
|DB1|**Adr_MSB**|||
|DB2|**Adr_LSB**<br>Lok-Adresse=(**Adr_MSB**& 0x3F) << 8 +**Adr_LSB**|||
|DB3|**111010MM**<br>**Option**...**0xE8**<br>**MM**... CVAdr_MSB|||
|DB4|**CVAdr_LSB**<br>CV-Adresse = (**MM**<< 8) +**CVAdr_LSB**<br>(0=CV1., 1=CV2, 255=CV256, usw.)|||
|DB5|0000**VPPP**<br>**PPP**... Bit-Position in CV<br>**V**... neuer Bit-Wert|||



Antwort von Z21: keine 

Dokumentenversion 1.13 

39/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_6.8 LAN_X_CV_POM_READ_BYTE_** 

### **Ab Z21 FW Version 1.22.** 

Mit folgendem Kommando kann eine CV eines Lokdecoders (Multi Function Digital Decoders gemäß NMRA S-9.2.1 Abschnitt C; Configuration Variable Access Instruction - Long Form) auf dem Hauptgleis gelesen werden (POM). Das geschieht im normalen Betriebsmodus, d.h. die Gleisspannung muss eingeschaltet sein, der normale Programmiermodus ist nicht aktiviert. RailCom muss in der Z21 aktiviert sein. Der zu lesende Fahrzeugdecoder muss RailCom beherrschen, CV28 bit 0 und 1 sowie CV29 bit 3 müssen im Lokdecoder auf 1 gesetzt sein (Zimo). 

|Anforderung an Z21:|
|---|



|**DataL**|**en**|**Heade**|**r**|**Data**||||||||
|---|---|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**DB4**|**DB5**|**XOR-Byte**|
|0x0C|0x00|**0x40**|0x00|**0xE6**|**0x30**|**POM-**|**Paramet**|**er**|||XOR-Byte|



<u>Die Daten für</u> **<u>POM-Parameter</u>** <u>sind folgendermaßen aufgebaut:</u> 

|**Position**|**Daten**|<br>**Bedeutung**|
|---|---|---|
|DB1|**Adr_MSB**||
|DB2|**Adr_LSB**|Lok-Adresse=(**Adr_MSB**& 0x3F) << 8 +**Adr_LSB**|
|DB3|**111001MM**|**Option**...**0xE4**<br>**MM**... CVAdr_MSB|
|DB4|**CVAdr_LSB**|CV-Adresse = (**MM**<< 8) +**CVAdr_LSB**<br>(0=CV1., 1=CV2, 255=CV256, usw.)|
|DB5|**0**|neuerCV-Wert|



Antwort von Z21: 

_6.4_ LAN_X_CV_NACK oder _6.5_ LAN_X_CV_RESULT _._ 

Dokumentenversion 1.13 

40/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_6.9 LAN_X_CV_POM_ACCESSORY_WRITE_BYTE_** 

### **Ab Z21 FW Version 1.22.** 

Mit folgendem Kommando kann eine CV eines Accessory Decoders (gemäß NMRA S-9.2.1 Abschnitt D, Basic Accessory Decoder Packet address for operations mode programming) auf dem Hauptgleis geschrieben werden (POM). Das geschieht im normalen Betriebsmodus, d.h. die Gleisspannung muss eingeschaltet sein, der normale Programmiermodus ist nicht aktiviert. Es gibt keine Rückmeldung. 

<u>Anforderung an Z21:</u> 

|**DataL**|**en**|**Heade**|**r**|**Data**<br>||||||||
|---|---|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**DB4**|**DB5**|**XOR-Byte**|
|0x0C|0x00|**0x40**|0x00|**0xE6**|**0x31 **|**POM-**|**Paramet**|**er**|||XOR-Byte|



<u>Die Daten für</u> **<u>POM-Parameter</u>** <u>sind folgendermaßen aufgebaut:</u> 

|**Position**|**Daten**|<br>**Bedeutung**|
|---|---|---|
|DB1|**aaaaa**|Decoder_Adresse MSB|
|DB2|**AAAACDDD**|Es gilt:**aaaaaAAAACDDD**= ((Decoder_Addresse & 0x1FF) << 4) | CDDD;<br>Falls**CDDD**=0000, dann bezieht sich die CV auf den ganzen Decoder.<br>Falls**C**=1, so ist**DDD**die Nummer des zu programmierenden Ausgangs.|
|DB3|**111011MM**|**Option**...**0xEC**<br>**MM**... CVAdr_MSB|
|DB4|**CVAdr_LSB**|CV-Adresse = (**MM**<< 8) +**CVAdr_LSB**<br>(0=CV1., 1=CV2, 255=CV256, usw.)|
|DB5|**Value**|neuerCV-Wert|



Antwort von Z21: keine 

### **_6.10 LAN_X_CV_POM_ ACCESSORY_WRITE_BIT_** 

### **Ab Z21 FW Version 1.22.** 

Mit folgendem Kommando kann ein Bit einer CV eines Accessory Decoders (gemäß NMRA S-9.2.1 Abschnitt D, Basic Accessory Decoder Packet address for operations mode programming) auf dem Hauptgleis geschrieben werden (POM). Das geschieht im normalen Betriebsmodus, d.h. die Gleisspannung muss eingeschaltet sein, der normale Programmiermodus ist nicht aktiviert. Es gibt keine Rückmeldung. 

<u>Anforderung an Z21:</u> 

|**DataL**|**en**|**Heade**|**r**|**Data**<br>||||||||
|---|---|---|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**DB4**|**DB5**|**XOR-Byte**|
|0x0C|0x00|**0x40**|0x00|**0xE6**|**0x31**|**POM-**|**Paramet**|**er**|||XOR-Byte|



<u>Die Daten für</u> **<u>POM-Parameter</u>** <u>sind folgendermaßen aufgebaut:</u> 

|**Position**|**Daten**|<br>**Bedeutung**|
|---|---|---|
|DB1|**aaaaa**|Decoder_Adresse MSB|
|DB2|**AAAACDDD**|Es gilt:**aaaaaAAAACDDD**= ((Decoder_Addresse & 0x1FF) << 4) | CDDD;<br>Falls**CDDD**=0000, dann bezieht sich die CV auf den ganzen Decoder.<br>Falls**C**=1, so ist**DDD**die Nummer des zu programmierenden Ausgangs.|
|DB3|**111010MM**|**Option**...**0xE8**<br>**MM**... CVAdr_MSB|
|DB4|**CVAdr_LSB**|CV-Adresse = (**MM**<< 8) +**CVAdr_LSB**<br>(0=CV1., 1=CV2, 255=CV256, usw.)|
|DB5|0000**VPPP**|**PPP**... Bit-Position in CV<br>**V**... neuer Bit-Wert|



Dokumentenversion 1.13 

41/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



Antwort von Z21: keine 

### **_6.11 LAN_X_CV_POM_ ACCESSORY_READ_BYTE_** 

### **Ab Z21 FW Version 1.22.** 

Mit folgendem Kommando kann eine CV eines Accessory Decoders (gemäß NMRA S-9.2.1 Abschnitt D, Basic Accessory Decoder Packet address for operations mode programming) auf dem Hauptgleis gelesen werden POM). Das geschieht im normalen Betriebsmodus, d.h. die Gleisspannung muss eingeschaltet sein, der normale Programmiermodus ist nicht aktiviert. RailCom muss in der Z21 aktiviert sein. Der zu lesende Accessory Decoder muss RailCom beherrschen. 

### <u>Anforderung an Z21:</u> 

|<br>**DataLen**<br>**Header**|**Data**||
|---|---|---|
||**X-Header**<br>**DB0**<br>**DB1**<br>**DB2**<br>**DB3**|**DB4**<br>**DB5**<br>**XOR-Byte**|
|0x0C<br>0x00<br>**0x40**<br>0x00|**0xE6**<br>**0x31 **<br>**POM-Parameter**|XOR-Byte|
|Die Daten für**POM-Paramet**<br> <br>|**er**sind folgendermaßen aufgebaut:<br>||
|**Position**<br>**Daten**|**Bedeutung**||
|DB1<br>**aaaaa**|Decoder_Adresse MSB||
|DB2<br>**AAAACDDD**|Es gilt:**aaaaaAAAACDDD**= ((Decoder_Addre<br>Falls**CDDD**=0000, dann bezieht sich die CV a<br>Falls**C**=1, so ist**DDD**die Nummer des betreff|sse & 0x1FF) << 4) | CDDD;<br>uf den ganzen Decoder.<br>enden Ausgangs.|
|DB3<br>**111001MM**|**Option**...**0xE4**<br>**MM**... CVAdr_MSB||
|DB4<br>**CVAdr_LSB**|CV-Adresse = (**MM**<< 8) +**CVAdr_LSB**<br>(0=CV1., 1=CV2, 255=CV256, usw.)||
|DB5<br>**0**|neuer CV-Wert||



Antwort von Z21: 

_6.4_ LAN_X_CV_NACK oder _6.5_ LAN_X_CV_RESULT _._ 

Dokumentenversion 1.13 

42/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_6.12 LAN_X_MM_WRITE_BYTE_** 

### **Ab Z21 FW Version 1.23.** 

Mit folgendem Kommando kann ein Register eines Motorola Decoders auf dem Programmiergleis überschrieben werden. 

|Anford|erung a|n Z21:||||||||
|---|---|---|---|---|---|---|---|---|---|
|**DataL**|**en**|**Heade**|**r**|**Data**||||||
|||||**X-Header**|**DB0**|**DB1**|**DB2**|**DB3**|**XOR-Byte**|
|0x0A|0x00|**0x40**|0x00|**0x24**|**0xFF**|**0**|**RegAdr**|**Value**|XOR-Byte|



Es gilt für **RegAdr** : 0=Register1, 1=Register2, …, 78=Register79. Es gilt 0 ≤ **Value** ≤ 255, aber einige Decoder akzeptieren nur Werte von 0 bis 80. 

### Antwort von Z21: 

_2.9_ LAN_X_BC_PROGRAMMING_MODE an Clients mit Abo, sowie das Ergebnis _6.3_ LAN_X_CV_NACK_SC oder _6.5_ LAN_X_CV_RESULT _._ 

**Anmerkung** : Das Programmieren von Motorola-Decodern war im ursprünglichen Motorola-Format nicht vorgesehen. Daher gibt es zum Programmieren von Motorola-Decodern kein genormtes und verbindliches Programmierverfahren. Für die Programmierung von Motorola Decodern wurde in der Z21 der später eingeführte, sogenannte „6021-Programmiermodus“ implementiert. Dieser erlaubt das Schreiben von Werten, jedoch nicht das auslesen. Ebenso kann der Erfolg der Schreibeoperation nicht überprüft werden (ausgenommen Kurzschlusserkennung). Dieses Programmierverfahren funktioniert für viele Decoder von ESU, Zimo und Märklin, jedoch nicht zwingend für alle MM-Decoder. Beispielsweise können Motorola-Decoder mit DIP-Schaltern nicht programmiert werden. Manche Decoder akzeptieren nur Werte von 0 bis 80, andere Werte von 0 bis 255 (siehe Decoder-Beschreibung). 

Da bei der Motorola-Programmierung vom Decoder keinerlei Rückmeldung über den Erfolg der Schreibeoperation kommt, ist hier die Meldung _LAN_X_CV_RESULT_ lediglich als _„MM Programmiervorgang beendet“_ und **nicht** als _„MM Programmiervorgang erfolgreich“_ zu verstehen. 

Beispiel: 

**`0x0A 0x00 0x40 0x00 0x24 0xFF 0x00 0x00 0x05 0xDE`** bedeutet: „Ändere die Lokdecoder-Adresse ( **Register1** ) auf **5** “ 

Dokumentenversion 1.13 

43/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_6.13 LAN_X_DCC_READ_REGISTER_** 

### **Ab Z21 FW Version 1.25.** 

Mit folgendem Kommando kann ein Register eines DCC Decoders im Registermodus (S-9.2.3 Service Mode Instruction Packets for Physical Register Addressing) auf dem Programmiergleis ausgelesen werden. 

<u>Anforderung an Z21:</u> 

|**DataLe**|**n**|**Header**|**Data**||||
|---|---|---|---|---|---|---|
||||**X-Header**|**DB0**|**DB1**|**XOR-Byte**|
|0x08|0x00|**0x40**<br>0x00|**0x22**|**0x11**|**REG**|XOR-Byte|



Es gilt für **REG** : 0x01=Register1, 0x02=Register2, …, 0x08=Register8. Es gilt 0 ≤ **Value** ≤ 255 

Antwort von Z21: _2.9_ LAN_X_BC_PROGRAMMING_MODE an Clients mit Abo, sowie das Ergebnis _6.3_ LAN_X_CV_NACK_SC oder _6.5_ LAN_X_CV_RESULT _._ 

**Anmerkung** : Das Programmieren im Registermodus wird nur für sehr alte DCC Decoder benötigt. Direct CV ist möglichst zu bevorzugen. 

### **_6.14 LAN_X_DCC_WRITE_REGISTER_** 

### **Ab Z21 FW Version 1.25.** 

Mit folgendem Kommando kann ein Register eines DCC Decoders im Registermodus (S-9.2.3 Service Mode Instruction Packets for Physical Register Addressing) auf dem Programmiergleis überschrieben werden. 

<u>Anforderung an Z21:</u> 

|**DataL**|**en**|**Heade**|**r**|**Data**|||||
|---|---|---|---|---|---|---|---|---|
|||||**X-Header**|**DB0**|**DB2**|**DB3**|**XOR-Byte**|
|0x09|0x00|**0x40**|0x00|**0x23**|**0x12**|**REG**|**Value**|XOR-Byte|



Es gilt für **REG** : 0x01=Register1, 0x02=Register2, …, 0x08=Register8. Es gilt 0 ≤ **Value** ≤ 255 

Antwort von Z21: _2.9_ LAN_X_BC_PROGRAMMING_MODE an Clients mit Abo, sowie das Ergebnis _6.3_ LAN_X_CV_NACK_SC oder _6.5_ LAN_X_CV_RESULT _._ 

**Anmerkung** : Das Programmieren im Registermodus wird nur für sehr alte DCC Decoder benötigt. Direct CV ist möglichst vorzuziehen. 

Dokumentenversion 1.13 

44/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **7 Rückmelder – R-BUS** 

Die Rückmeldemodule (Bestellnummer 10787, 10808 und 10819) am R-BUS können mit den folgenden Kommandos ausgelesen und konfiguriert werden. 

### **_7.1 LAN_RMBUS_DATACHANGED_** 

Änderung am Rückmeldebus von der Z21 an den Client melden. 

Diese Meldung wird asynchron von der Z21 an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000002 

- oder den Rückmelder-Status explizit angefordert hat, siehe unten _7.2_ LAN_RMBUS_GETDATA. 

<u>Z21 an Client:</u> 

|**DataLen**|**Header**|**Data**||
|---|---|---|---|
|0x0F<br>0x00|**0x80**<br>0x00|**Gruppenindex**(1 Byte)|**Rückmelder-Status**(10 Byte)|



**Gruppenindex:** 0 ... Rückmeldemodule mit Adressen von   1 bis 10 

1 ... Rückmeldemodule mit Adressen von 11 bis 20 

**Rückmelder-Status:** 1 Byte pro Rückmelder, 1 bit pro Eingang. 

Die Zuordnung Rückmelder-Adresse und Byteposition ist statisch aufsteigend. 

Beispiel: 

GruppenIndex = 1 und Rückmelder-Status = 0x01 0x00 0xC5 0x00 0x00  0x00 0x00 0x00 0x00 0x00 bedeutet „Rückmelder 11, Kontakt auf Eingang 1; Rückmelder 13, Kontakt auf Eingang 8,7,3 und 1“ 

### **_7.2 LAN_RMBUS_GETDATA_** 

Anfordern des aktuellen Rückmelder-Status. 

|Anforderung an|Z21:|||
|---|---|---|---|
|**DataLen**|**Header**||**Data**|
|0x05<br>0x00|**0x81**|0x00|**Gruppenindex**(1 Byte)|



### **Gruppenindex:** siehe oben 

Antwort von Z21: Siehe oben _7.1_ LAN_RMBUS_DATACHANGED 

Dokumentenversion 1.13 

45/78 

06.11.2023 





<!-- Start of picture text -->
Client ‘Ruckmeldemodul<br>10787<br>| | R-BUS Normalbetrieb .<br>Actor||alle Module vom R-BUS abstecken | 5!|<br>| |<br>\|||<br>\| | ||<br>Pragrammiervargang starten LAN _RMBUS_PROGRAMMODULE |<br>| Adresse #7 auswahlen und \ \ |<br>\ Adresse=7 Programmierbefehl "Adresse=7" |<br>|<br>|<br>Programmierbefehl "Adresse=7" |<br>| |<br>| Das zu programmierende Modul am R-BUS anstecken |<br>| Programmierbefehl "Adresse=7"<br>| Das Modul wird pragrammiert, 4<br>| LEDs leuchten zur Bestatigung<br>|\ Programmierbefehl "Adresse=7" |<br>|<br>| Program miervorgang Programmierbefehl "Adresse=7" |<br>bestatigen LAN _RMBUS_PROGRAMMODULE<br>\ \ Adresse=0 R-BUS Normalbetrieb ~ |<br>| Po<br>| |<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



## **8 RailCom** 

Die Z21 unterstützt RailCom durch: 

- Erzeugung der RailCom-Lücke am Gleissignal. 

- Globaler Empfänger in der Z21. 

- Lokale Empfänger, z.B. in den Belegtmeldern 10808 für die Lokerkennung. Zusätzlich können beim 10808 die Daten vom RailCom-Kanal 2 über CAN an die Z21 weitergeleitet und dort ausgewertet werden ab FW V1.29. 

- POM-Lesen. 

Siehe auch 6.8 LAN_X_CV_POM_READ_BYTE ab FW V1.22. 

- Lokadressen-Erkennung bei Belegtmeldern. 

   - Siehe 9.5 LAN_LOCONET_DETECTOR ab V1.22 und 10.1 LAN_CAN_DETECTOR ab V1.30. 

- Decoder-Geschwindigkeit (siehe unten) ab FW V1.29. 

- Decoder-QoS (siehe unten) ab FW V1.29. 

Um diese Leistungsmerkmale nutzen zu können, muss der Decoder RailCom-fähig, CV28 und CV29 korrekt konfiguriert und die Option „RailCom“ in den Einstellungen der Z21 aktiviert sein. 

Ob und in welcher Form ein Decoder die Geschwindigkeit, QoS und POM unterstützt, hängt von der Decoder-Firmware ab. 

### **_8.1 LAN_RAILCOM_DATACHANGED_** 

Diese Meldung wird von der Z21 ab FW Version 1.29 an die Clients als Antwort auf das Kommando 8.2 LAN_RAILCOM_GETDATA gesendet. 

Sie wird aber auch ungefragt an Clients gesendet, wenn 

- sich die entsprechenden RailCom-Daten tatsächlich verändert haben 

- und der betreffende Client den entsprechenden Broadcast aktiviert hat (siehe **2.16** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000004) und der betreffende Client die Lok-Adresse mit 4.1 LAN_X_GET_LOCO_INFO abonniert hat 

- oder der betreffende Client den Broadcast 0x00040000 abonniert hat (d.h. RailCom-Daten aller Loks, für PC-Steuerungen). 

### <u>Z21 an Client:</u> 

|**DataLen**||**Header**<br>**Dat**|**a**|
|---|---|---|---|
|0x11|0x00<br>**0**|**x88**<br>0x00<br>**Rail**|**ComDaten**|
|Die Struktur**R**|**ailComD**|**aten**ist wie folgt au|fgebaut (die 16-bit und 32-bit Werte sind little endian):|
|**Byte Offset**|**Typ**|**Name**||
|0|UINT16|LocoAddress|Adresse des erkannten Decoders|
|2|UINT32|ReceiveCounter|Empfangszähler in Z21|
|6|UINT16|ErrorCounter|Empfangsfehlerzähler in Z21|
|8|UINT8|reserved||
|9|UINT8|Options|Flags Bitmaske:<br>`#define rcoSpeed1`<br>`0x01// CH7 subindex 0`<br>`#define rcoSpeed2`<br>`0x02// CH7 subindex 1`<br>`#define rcoQoS`<br>`0x04// CH7 subindex 7`|
|10|UINT8|Speed|Geschwindigkeit 1 oder 2 (falls vom Decoder unterstützt)|
|11|UINT8|QoS|Quality of Service (falls vom Decoder unterstützt)|
|12|UINT8|reserved||



Die Struktur kann in Zukunft vergrößert werden, daher ist unbedingt bei der Auswertung DataLen zu berücksichtigen. 

Dokumentenversion 1.13 

47/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_8.2 LAN_RAILCOM_GETDATA_** 

RailCom-Daten von Z21 anfordern ab FW V1.29: 

|Anforderung an<br>|Z21:<br> <br>|
|---|---|
|**DataLen**|**Header**<br>**Data**|
|0x07<br>0x00|**0x89**<br>0x00<br>**Typ**8 bit<br>**LocoAdress**16 (bit little endian)|
|**Typ**|0x01 = RailCom-Daten für gegebene Lokadresse anfordern|
|**LocoAddress**|Lokadresse<br>0=nächste Lok im Ringbuffer anfragen|



Antwort von Z21: Siehe oben _8.2_ LAN_RAILCOM_DATACHANGED 

Dokumentenversion 1.13 

48/78 

06.11.2023 





<!-- Start of picture text -->
dain || LAN_SET_ BROADCAST| FLAGS 0x01000000 =I| !|<br>| | LAN_SET| BROADCAST FLAGS ox01 000040| |<br>|||||<br>||__Lokin Slot #1 dispatchen | : |<br>| | | | |<br>:iS data=(OP®_MOVE_SLOTSLAN LOCONET_Z21_RX0x01,0x00) ——\ SGTvi = \<br>| \| Sjata=(OPC_MOVE_SLOTS| LAN_LOCONET Z21_RXOx01,0x00) || \\<br>|! \ ek\  (SBE ae \ OPC_SL_RD_DATA A OxOE 0x01... |<br>| fs data=(OPC_S L_RD_DATA Ox0E,0x01....)<br>| f | LAN _LOCONET Z21_Tx \<br>| \| Sjata=(OPC_S L_RD_DATA OxOE,Ox01....) || \|<br>||||<br>|| | | |<br>\ FastClock-Zeit) einstellen : | \ \<br>09:30, aes \ LAN_LOCONET FROM _LAN |<br>| \ ;data=(OPC_SL_WR_DATA OXOE,0Xx75,7 OPC SL_WR_ DATA Ox0E,0x7B,....|<br>; | LAN ILOCONET FROM_LAN |<br>| iS data=(OPCl_SL_WR_DATA Ox0E,0x7B...) \ \<br>! | | | |<br>iS dat=(OPC_LONG_ACK)LAN LOCONET Z21_TXx<br>| “LAN _LOCONET Z21_TX<br>| \ fe data=(OPC_LONG_ACK) | \<br>| | | | |<br>| 1 * 1 1<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



Wägen Sie daher beim Abonnieren der LocoNet-Meldungen genau ab, ob die Broadcast Flags 0x02000000 (Loks) und 0x04000000 (Weichen) auch wirklich für Ihre Applikation unbedingt notwendig sind. Verwenden Sie vor allem zum konventionellen Fahren und Schalten nach wie vor soweit wie möglich die bereits beschriebenen LAN-Befehle aus den Kapiteln **_4_** Fahren, **_5_** Schalten und **_6_** Decoder CV Lesen und Schreiben. 

Das eigentliche LocoNet-Protokoll wird in dieser Spezifikation nicht weiter beschrieben. Bitte wenden Sie sich dazu direkt an Digitrax oder ggf. an den Hersteller der jeweiligen LocoNet-Hardware, speziell wenn dieser das LocoNet-Protokoll für Konfiguration etc. eigenmächtig erweitert haben sollte. 

### **_9.1_ LAN_LOCONET_Z21_RX** 

### **Ab Z21 FW Version 1.20.** 

Diese Meldung wird asynchron von der Z21 an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flags 0x01000000, 0x02000000 bzw. 0x04000000. 

- und von der Z21 eine Meldung am LocoNet-Bus empfangen worden ist. 

<u>Z21 an Client:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|||||**LocoNet Meldung inkl. CKSUM**|
|0x04+n|0x00|**0xA0**|0x00|n Bytes|



### **_9.2_ LAN_LOCONET_Z21_TX** 

### **Ab Z21 FW Version 1.20.** 

Diese Meldung wird asynchron von der Z21 an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flags 0x01000000, 0x02000000 bzw. 0x04000000. 

- und von der Z21 eine Meldung auf den LocoNet-Bus geschrieben worden ist. 

### <u>Z21 an Client:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|||||**LocoNet Meldung inkl. CKSUM**|
|0x04+n|0x00|**0xA1**|0x00|n Bytes|



Dokumentenversion 1.13 

50/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_9.3_ LAN_LOCONET_FROM_LAN** 

### **Ab Z21 FW Version 1.20.** 

Mit dieser Meldung kann ein LAN-Client eine Meldung auf den LocoNet-Bus schreiben. 

Diese Meldung wird außerdem asynchron von der Z21 an einen Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flags 0x01000000, 0x02000000 bzw. 0x04000000. 

- und ein **anderer** LAN-Client über die Z21 eine Meldung auf den LocoNet-Bus geschrieben hat. 

|LAN-Client an Z2<br>**DataLen**|1, bzw. Z21 an LA<br>**Header**|N-Client:<br>**Data**|
|---|---|---|
|||**LocoNet Meldung inkl. CKSUM**|
|0x04+n<br>0x00|**0xA2**<br>0x00|n Bytes|



### **9.3.1 DCC Binary State Control Instruction per LocoNet OPC_IMM_PACKET** 

**Ab Z21 FW Version 1.42** wird zum Schalten von Binary States anstelle er wie folgt beschriebenen Methode das neue Kommando _4.3.3 LAN_X_SET_LOCO_BINARY_STATE_ empfohlen. Der nun folgende, inzwischen etwas veraltete Absatztext bleibt zwecks Vollständigkeit trotzdem bestehen: 

**Ab FW Version V1.25** können mittels LAN_LOCONET_FROM_LAN und dem LocoNet Befehl OPC_IMM_PACKET beliebige DCC Pakete am Gleisausgang generiert werden, darunter auch die Binary State Control Instruction (auch „F29…F32767“ genannt). Das gilt auch für die weiße z21, die zwar keine physikalische LocoNet Schnittstelle aufweist, aber sehr wohl über einen virtuellen LocoNet Stack verfügt. 

Zum Aufbau des OPC_IMM_PACKET siehe LocoNet Spec (auch in personal edition zu Lernzwecken). Zum Aufbau der Binary State Control Instruction siehe NMRA S-9.2.1 Abschnitt Feature Expansion Instruction. 

Dokumentenversion 1.13 

51/78 

06.11.2023 





<!-- Start of picture text -->
LocoNet Master a<br>||<br>Actor ee|| LAN_SET_BROADCAST_FLAGSa0x01000000 | |<br>Lok#3 befindet IN |<br>LokiAdresse #3 dispatch vorbergiten \ sich z.B. in Slot #4 \<br>LAN_LOCONET DISPATCH ADDR !<br>\ \ Adresse=3 \ |<br>|||| LAN _LOCONET DISPATCH ADDR #3 || iAbFWe=1.22 ‘| |\<br>| | Aaresse= crgepnis=4 (Oh i \<br>||\<br>|\ Lok am FRED Ubernehmen | 5 |<br>||'\<br>|OPC _MOVE SLOTS 0x00,0x00_!<br>le LANLoconerzipx SS aes<br>| depot ten |__OPC_SL_RD_DATA Ox0E,0x04,... _!<br>I, LAN _LOCONET Z21_Tx EEE<br>e data=(OPC_SL_RD_DATA OxOE,0x04 | !<br>| L- OPC_SL_WR_DATA OXx0E,0x04,..._!<br>\ 13 LAN LOCONET Z21_ Rx iS (Throttle-IDin Sloteintragen, ...) |<br>data=(OPC_SL_WR_DATA O0x0E,0x04....) i OPC LONG ACK |<br>\ L LAN LOCONET Z21_Tx 1<br>data=(OPC_LONG_ACI \ Lok #3 kann ab jetzt \<br>\ \ mit FRED gesteuert \<br>! \| Lok mit FRED steuern \i werden... >!\|<br>A 1 | 1<br><!-- End of picture text -->

Z21 LAN Protokoll Spezifikation 



### **_9.5_ LAN_LOCONET_DETECTOR** 

### **Ab Z21 FW Version 1.22.** 

Falls eine Applikation im LAN Client einen LocoNet Gleisbesetztmelder unterstützen möchte, gibt es dafür zwei Möglichkeiten. Die erste wäre, mittels **_9.1_** _LAN_LOCONET_Z21_RX_ die LocoNet-Pakete zu empfangen und die entsprechenden LocoNet-Meldungen selbständig zu verarbeiten. Das setzt aber eine entsprechend genaue Kenntnis des LocoNet Protokolls voraus. 

Deswegen wurde die folgende Alternative geschaffen, mit denen man als LAN Client **sowohl** den Belegtstatus **abfragen** kann, **als auch** über eine Änderung des Belegtstatus **asynchron informiert** werden kann, ohne in die Tiefen des LocoNet-Protokolls einsteigen zu müssen. 

**Information** : bitte beachten Sie folgenden wesentlichen Unterschied zwischen dem Roco Rückmeldemodul 10787 am R-BUS (siehe **_7_** Rückmelder – R-BUS) und LocoNet Gleisbesetztmeldern: 

- 10787 basiert auf mechanisch betätigten Schaltkontakten, die pro Achse des darüber fahrenden Zugs geschlossen und wieder geöffnet werden können. 

- LocoNet Gleisbesetztmelder basieren üblicherweise auf exakter Strommessung am überwachten Gleisabschnitt bzw. auf fortgeschrittene Technologien (Transponder, Infrarot, RailCom, ..), um den Besetzt-Zustand des Gleises zuverlässig ermitteln zu können. Während des Normalbetriebs wird im Idealfall nur eine Meldung bei der Änderung des Besetztzustands generiert. 

Mit folgendem Kommando kann der Status eines oder mehrerer Gleisbesetztmelder abgefragt werden. 

|Anforder<br>|ung an<br>|Z21:<br>|<br>|
|---|---|---|---|
|**DataLen**||**Hea**|**der**<br>**Data**|
|0x07|0x00|**0xA**|**4**<br>0x00<br>**Typ**8 bit<br>Reportadresse 16 bit (**little endian**)|
|**Typ**||**0x80**|Abfrage mittels „Stationary Interrogate Request“ (**SIC**) gemäß Digitrax-Verfahren.<br>Dieses Verfahren ist auch bei den Belegtmeldern von Blücher-Elektronik zu<br>verwenden. Die Reportadresse ist hier 0 (don't care).|
|||**0x81**|Abfrage mittels sogenannter**Reportadresse**für Uhlenbrock-Besetztmelder.<br>Diese Reportadresse kann vom Anwender z.B. beim UB63320 über LNCV 17 im<br>Besetztmelder konfiguriert werden. Der Default-Wert ist dort 1017.<br>Die Reportadresse wird beim Typ 0x81 nur zum Abfragen verwendet und ist<br>**nicht**mit der**Rückmelderadresse**zu verwechseln.<br>**Hinweis**: Am LocoNet-Bus ist diese Abfrage über Weichenstellbefehle<br>implementiert, deswegen ist der Wert gemäß LocoNet**um 1 dekrementiert**zu<br>übergeben. Beispiel:<br>**`0x07 0x00 0xA4 0x00 0x81 0xF8 0x03`**<br>bedeutet: „fordere Status aller Besetztmelder mit Reportadresse 1017 an<br>(Reportadresse = 1017 =**0x03F8**+1 = 1016 + 1)“|
|||**0x82**|**Statusabfrage für LISSY ab Z21 FW Version 1.23**<br>Bei Uhlenbrock LISSY entspricht  hier die Reportadresse allerdings wieder der<br>Rückmelderadresse. Die Art der darauf folgenden Rückmeldung(en) hängt stark<br>vom konfigurierten Betriebsmodus des LISSY-Empfängers ab. Über die<br>umfangreichen Einstellmöglichkeiten des LISSY-Empfängers können Sie sich<br>im LISSY-Handbuch informieren.|



Bitte beachten Sie, dass bei einer einzigen Anfrage ggf. mehre Besetztmelder gleichzeitig angesprochen werden, und daher in der Regel mehrere Antworten zu erwarten sind. Abhängig vom Hersteller des Besetztmelders kann nach dieser Anforderung teilweise der Status ein und des selben Eingangs mehrmals gemeldet werden! 

Dokumentenversion 1.13 

53/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### Antwort von Z21: 

### <u>Z21 an Client:</u> 

|**DataLen**|**Header**||**Data**|||
|---|---|---|---|---|---|
|0x07 +**_n_**<br>0x00|**0xA4**|0x00|**Typ**8 bit|**Rückmelderadresse**16 bit (**little**<br>**endian**)|**Info**[**_n_**]|



Diese Meldung wird asynchron von der Z21 an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x08000000 

- und die Z21 eine entsprechende Meldung von einem Gleisbesetztmelder empfangen hat, **aufgrund einer Statusänderung** an dessen Eingang, **oder aufgrund einer expliziten Abfrage** durch einen LAN Client mittels oben beschriebenen Kommandos. 

**Rückmelderadresse** Jedem Eingang des Besetztmelders ist eine eigenen Rückmelderadresse zugeordnet, welche vom Anwender konfiguriert werden kann (z.B. bei Uhlenbrock und Blücher mittels LNCV) und den überwachten Block eindeutig beschreibt. 

**Info[** **_n_ ]** Byte-Array; Inhalt und Länge **_n_** abhängig von **Typ** , siehe unten 

**Typ 0x01** Für Besetztmelder-Typen wie Uhlenbrock 63320 oder Blücher GBM16 **XL** , welche nur den Status „belegt“ und „frei“ melden (LocoNet OPC_INPUT_REP, X=1). 

### **_n=1_** 

Status des zur Rückmelderadresse gehörenden Eingangs steht in **Info[0]: Info[0]** = **0** ... Sensor ist **LO** (“frei”) **Info[0]** = **1** ... Sensor ist **HI** (“belegt”) 

### **0x02 Transponder Enters Block** 

### **0x03 Transponder Exits Block** 

Für Besetztmelder Typen wie Blücher GBM16 **XN** etc welche die Information (z.B. Lokadresse) über das Fahrzeug im Block an die Zentrale melden (mittels LocoNet  OPC_MULTI_SENSE Transponding Encoding von Digitrax). Es wird neben der Rückmelderadresse noch eine sogenannte Transponderadresse übertragen. Die Transponderadresse identifiziert das im Block befindliche Fahrzeug. Im Fall vom GBM16 **XN** ist das die Lok-Adresse, welche vom Belegtmelder mittels RailCom ermittelt worden ist. 

### **_n=2_** 

Die Transponderadresse befindet sich in **Info[0]** und **Info[1]** , 16 Bit little endian: **Info[0]** ... Transponderadresse Low Byte **Info[1]** ... Transponderadresse High Byte 

Anmerkung: aufgrund einer Schwäche der LocoNet Spezifikation gibt es beim Wertebereich von OPC_MULTI_SENSE einen Interpretationsspielraum, welcher die Hersteller der Belegtmelder im unklaren lässt.. Daher gibt es im Fall von GBM16 **XN** nach unseren Erfahrungen folgendes zu beachten: 

- Zur Rückmelderadresse muss +1 addiert werden, um auf jene 

   - Rückmelderadresse zu bekommen, welche im GBM16 **XN** konfiguriert ist. 

- Je nach Konfiguration des GBM16 **XN** wird im Bit unter der Maske 0x1000 die Richtung des Fahrzeugs auf dem Gleis codiert. Diese Konfiguration wird von uns nicht empfohlen, das dieses Bit mit dem Adressraum für lange LokAdressen kollidiert! 

Dokumentenversion 1.13 

54/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **0x10 LISSY Lokadresse ab Z21 FW 1.23.** 

Diese Meldung wird an den Z21 LAN Client geschickt, wenn ein Uhlenbrock LISSY-Empfänger ein Fahrzeug meldet, welches mit einem LISSY-Sender ausgerüstet ist, und der LISSY-Empfänger auf das „Übergabeformat (ÜF) Uhlenbrock“ (LNCV 15=1) konfiguriert ist. Weiters hängt diese Meldung stark vom konfigurierten Betriebsmodus (LNCV2, …) des Lissy-Empfängers ab. Siehe LISSY-Handbuch. 

### **_n=3_** 

Die Lokadresse befindet sich in Info[0] und Info[1], 16 Bit little endian: **Info[0]** ... Lokadresse Low Byte **Info[1]** ... Lokadresse High Byte Loks haben einen Wertebereich von 1..9999 Wagen haben einen Wertebereich von 10000 bis 16382 

**Info[2]** ... Zusatzinformation mit folgenden Bits: 0 **DIR1 DIR0** 0 **K3 K2 K1 K0 DIR1** =0: **DIR0** ist zu ignorieren **DIR1** =1: **DIR0** =0 ist vorwärts, **DIR0** =1 ist rückwärts **K3..K0** : 4 Bit Klasseninformation, welche im LISSY-Sender hinterlegt worden ist. 

### - <u>Beispielkonfiguration für Lissy Empfänger 68610:</u> 

|<br>**LNCV**|<br>**Wert**|<br>**Kommentar**|
|---|---|---|
|2|98|optionaler Modul-Reset: setzt alle LNCV auf 0, außer LNCV 0<br>und 1 (Adresse)|
|2|0|Grundfunktion: Auslesen der Lokdaten über Doppelsensor mit<br>Richtungsinformation|
|15|1|Sende Übergabeformat Uhlenbrock ans LocoNet|



### **0x11 LISSY Belegtzustand ab Z21 FW 1.23.** 

Diese Meldung wird an den Z21 LAN Client geschickt, wenn ein Uhlenbrock LISSY-Empfänger eine Blockzustandsmeldung im „Übergabeformat (ÜF) Uhlenbrock“ versendet. Siehe LISSY-Handbuch. 

### **_n=1_** 

Status des zur Rückmelderadresse gehörenden Blocks steht in Info[0]: **Info[0]** = **0** ... Block ist frei **Info[0]** = **1** ... Block ist belegt 

### - <u>Beispielkonfiguration für Lissy Empfänger 68610:</u> 

|<br>**LNCV**|<br>**Wert**|<br>**Kommentar**|
|---|---|---|
|2|98|optionaler Modul-Reset: setzt alle LNCV auf 0, außer LNCV 0<br>und 1 (Adresse)|
|2|22|**Automatikfunktion mit Blockzustandsmeldung:**<br>**Aufenthaltsstelle zeitgesteuert**|
|3|2|Automatik aktiv in beiden Fahrtrichtungen|
|4|3|Aufenthaltszeit 3 Sekunden|
|10|2|Blockoption:<br>Blockzustandsänderung auf „frei“nach 2 Sekunden<br>|
|15|1|Sende Übergabeformat (ÜF) Uhlenbrock ans LocoNet|



Dokumentenversion 1.13 

55/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **0x12 LISSY Geschwindigkeit ab Z21 FW 1.23.** 

Diese Meldung wird an den Z21 LAN Client geschickt, wenn ein Uhlenbrock LISSY-Empfänger für die Geschwindigkeitsmessung konfiguriert ist. Siehe LISSY-Handbuch. 

### **_n=2_** 

Die Geschwindigkeit befindet sich in Info[0] und Info[1], 16 Bit little endian: **Info[0]** ... Geschwindigkeit Low Byte **Info[1]** ... Geschwindigkeit High Byte 

### - <u>Beispielkonfiguration für Lissy Empfänger 68610:</u> 

|<br>**LNCV**|<br>**Wert**|<br>**Kommentar**|
|---|---|---|
|2|98|optionaler Modul-Reset:<br>setzt alle LNCV auf 0, außer LNCV 0 und 1 (Adresse)|
|2|0|Grundfunktion: Auslesen der Lokdaten über Doppelsensor mit<br>Richtungsinformation|
|**14**|**15660**|**Geschwindigkeit Skalierungsfaktor =**<br>**1566 (Maßstab H0)* 10mm (Sensorabstand)**<br>|
|15|1|Sende Übergabeformat (ÜF) UhlenbrockansLocoNet|



Anm. **Typ** wird je nach Bedarf in Zukunft noch um weitere IDs erweitert werden. 

Dokumentenversion 1.13 

56/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **10 CAN** 

### **_10.1_ LAN_CAN_DETECTOR** 

### **Ab Z21 FW Version 1.30.** 

Der Roco CAN-Belegtmelder 10808 wird ab FW Version 1.30 unterstützt. Der Belegtmelder kann vom LAN Client auf vier verschiedene Weisen verwendet werden: 

1. **R-BUS-Emulation** : der CAN-Belegtmelder wird in der Z21 Firmware als R-BUS-Melder an den LAN-Client weitergeleitet. Der LAN-Client kann den CAN-Belegtmelder verwenden, wie es in Kapitel **7** Rückmelder – R-BUS beschrieben ist. 

2. **LocoNet-Emulation** : der CAN-Belegtmelder wird in der Z21 Firmware als LocoNet-Melder an den LAN-Client weitergeleitet. Der LAN-Client kann den CAN-Belegtmelder verwenden, wie es in Kapitel **9.5** LAN_LOCO_NET_DETECTOR  beschrieben ist (Typ 0x01 „belegt/frei“ und die Lokadresse mittels Typ 0x02 und 0x03 „Transponder Enters Block, Transponder Exits Block“). 

3. **LISSY-Emulation** : der CAN-Belegtmelder wird in der Z21 Firmware durch LISSY/MarcoMeldungen emuliert. Der LAN-Client kann den CAN-Belegtmelder verwenden, wie es in Kapitel **9.5** LAN_LOCO_NET_DETECTOR  beschrieben ist (Typ 0x10 „Lokadresse“ und Typ 0x11 „Belegtzustand“). 

4. Direkter Zugriff durch den Befehl **LAN_CAN_DETECTOR** (siehe unten). 

Die Art der Emulation kann über das Z21 Maintenance Tool konfiguriert werden. Die Werkseinstellung ist: **R-BUS-Emulation=ein** , **LocoNet-Emulation=ein** , LISSY-Emulation=aus. 

Die schnellste und bezüglich Speicher und Bandbreite schonendste Methode ist jedoch der direkte Zugriff durch den Befehl **LAN_CAN_DETECTOR 0xC4** . Das empfiehlt sich vor allem dann, wenn sehr viele CAN-Belegtmelder gleichzeitig verendet werden sollen. Mit folgendem Kommando kann der Status der CAN-Belegtmelder direkt abgefragt werden: 

|Anforder<br>|ung<br>|an Z21:<br>|||
|---|---|---|---|---|
|**DataLen**||**Header**|**Data**||
|0x07|0x|00<br>**0xC4**<br>0x00|**Typ** 8 bit|**CAN-NetworkID**16 bit (little endian)|
|**Typ**||**0x00**Abfrage des<br>Die CAN-Ne<br>Beispiel:<br>**`0x07 0x0`**|CAN-Belegtmelders<br>tworkID**0xD000**bed<br>**`0 0xC4 0x00 0x`**|mit der gegeben CAN-NetworkID.<br>eutet „**alle CAN-Belegtmelder**“.<br>**`00 0x00 0xD0`**|
|||bedeutet: „f|ordere Status aller C|AN-Belegtmelder an“|



Bitte beachten Sie, dass bei einer einzigen Anfrage mehrere CAN-Belegtmelder gleichzeitig angesprochen werden, und daher in der Regel mehrere Antworten zu erwarten sind. Es kann der Status ein und desselben Eingangs je nach Konfiguration der Emulation auch mehrmals gemeldet werden! 

Dokumentenversion 1.13 

57/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### Antwort von Z21: 

### <u>Z21 an Client:</u> 

|**DataLen**|**Header**||**Data**||||||
|---|---|---|---|---|---|---|---|---|
|0x0E<br>0x00|**0xC4**|0x00|**NId**|**Addr**|**Port**|**Typ**|**Value1**|**Value2**|
||||16 bit|16 bit|8 bit|8 bit|16 bit|16 bit|



Diese Meldung wird asynchron von der Z21 an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00080000 

- und die Z21 eine entsprechende Meldung vom CAN-Belegtmelder empfangen hat, **aufgrund einer Statusänderung** an dessen Eingang, **oder aufgrund einer expliziten Abfrage** durch einen LAN-Client mittels oben beschriebenen Kommandos. 

Alle 16 bit Werte sind little endian codiert. 

**NId** Unveränderbare CAN-NetworkID des Belegtmelders. 

**Addr** Konfigurierbare Moduladresse des Belegtmelders. Jeder CAN-Belegtmelder hat eine Moduladresse, welche vom Anwender eingestellt werden kann. 

**Port** Eingang des CAN-Belegtmelders (0 bis 7) 

**Typ 0x01 Belegtstatus** des Eingangs (frei, besetzt, Überlast) 

**0x11** 1. und 2. erkannte **Lokadresse** am Eingang **0x12** 3. und 4. erkannte **Lokadresse** am Eingang 

… **0x1F** 29. und 30. erkannte **Lokadresse** am Eingang 

Der Wert von Value1 und Value2 hängt vom Typ ab. 

|**Falls Typ = 0x01 (Belegtst**|**atus):**|
|---|---|
|**Value1**<br>**0x0000**|F**rei, ohne Spannung**|
|**0x0100**|**Frei, mit Spannung**|
|**0x1000**|**Besetzt, ohne Spannung**|
|**0x1100**|**Besetzt, mit Spannung**<br>|
|**0x1201**|**Besetzt, Überlast 1**<br>|
|**0x1202**|**Besetzt, Überlast 2**<br>|
|**0x1203**|**Besetzt, Überlast 3**|



**Falls Typ = 0x11 bis 0x1F (RailCom Lokadressen):** Typ 0x11 bis 0x1F bilden eine Liste von Lokadressen. Diese Fahrzeugliste endet mit Lokadresse=0. 

**Value1** Erste erkannte Lokadresse im Abschnitt inkl. Richtungsinformation. 

- 0 = keine Lokadresse erkannt (z.B. bei nicht-RailCom-fähigem Decoder, oder keine Lok) bzw. Ende der Lokadressen-Liste 

**Value2** Zweite erkannte Lokadresse im Abschnitt inkl. Richtungsinformation. 

0 = keine Lokadresse erkannt bzw. Ende der Lokadressen-Liste 

In den obersten beiden Bits von Value1 bzw. Value2 ist die Richtungsinformation codiert: 

- 0 x Keine Richtung erkannt 

- 1 0 Fahrzeug ist vorwärts auf das Gleis gestellt worden 

- 1 1 Fahrzeug ist rückwärts auf das Gleis gestellt worden 

- In den untersten 14 Bits steht die Lokadresse. 

Dokumentenversion 1.13 

58/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_10.2_ CAN Booster** 

### **Ab Z21 FW Version 1.41.** 

Die LAN-Befehle für das CAN Booster Management mit den Roco CAN-Booster 10806, 10807 und 10869 werden ab FW Version 1.41 unterstützt. Die folgenden Befehle funktionieren selbstverständlich nur, wenn diese Booster über den CAN-Bus (= nicht per B-BUS) mit der Z21 verbunden sind. 

### **10.2.1 LAN_CAN_DEVICE_GET_DESCRIPTION** 

Bezeichnung aus CAN-Booster auslesen. 

Im CAN-Booster kann vom Anwender ein Name (Freitext) hinterlegt werden, damit er das Gerät später leichter wieder identifizieren kann. 

|Anforderung an<br>**DataLen**|Z21:<br>**Header**||**Data**|
|---|---|---|---|
|0x06<br>0x00|**0xC8**|0x00|**NId**16 bit|



**NId** ist die CAN-NetworkID des gewünschten Boosters (16 bit little endian, 0xC101 bis 0xC1FF). Siehe auch weiter unten **_10.2.3_** LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD. 

|Antwort von Z21|:||||
|---|---|---|---|---|
|**DataLen**|**Header**||**Data**||
|0x16<br>0x00|**0xC8**|0x00|**NId**16 bit|UINT8**Name**[16]|



**Name** entspricht der hinterlegten Bezeichnung als nullterminierter String. Der String sollte gemäß **ISO 8859-1** ( _Latin-1_ ) codiert sein. 

**Hinweis** : nicht zwei LAN_CAN_BOOSTER_GET_DESCRIPTION schnell hintereinander senden, sondern zuerst die Antwort abwarten und erst danach den zweiten Request absenden! 

**Hinweis:** Mit **_10.2.3_** LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD bekommen Sie die NetworkIDs aller im System angeschlossenen CAN-Booster. 

### **10.2.2 LAN_CAN_DEVICE_SET_DESCRIPTION** 

Bezeichnung im CAN- Booster überschreiben. 

|Anforderung an<br>**DataLen**|Z21:<br>**Header**||**Data**||
|---|---|---|---|---|
|0x16<br>0x00|**0xC9**|0x00|**NId**16 bit|UINT8 **Name**[16]|



**NId** ist die CAN-NetworkID des gewünschten Boosters (16 bit little endian, 0xC101 bis 0xC1FF). Siehe auch weiter unten **_10.2.3_** LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD. 

**Name** entspricht der zu hinterlegenden Bezeichnung als nullterminierter String. Der String sollte gemäß **ISO 8859-1** ( _Latin-1_ ) codiert sein. Füllen Sie ggf. den Rest von Data mit 0x00 auf. Nach dem 16. Zeichen wird in der Zentrale automatisch abgeschnitten. 

**Nicht erlaubte Zeichen sind das Anführungszeichen “ (0x22) und der Backslash \ (0x5C)** . 

Antwort von Z21: Keine 

Dokumentenversion 1.13 

59/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **10.2.3 LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD** 

Systemzustand des CAN-Boosters an den Client melden. Diese Meldung kommt pro CAN-Booster und Booster-Ausgang circa einmal pro Sekunde. 

Diese Meldung wird asynchron vom der Zentrale an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00020000 

- und mindestens ein Booster über CAN mit der Zentrale verbunden ist. 

### <u>Z21 an Client:</u> 

|**DataLen**<br>**Head**|**er**|**Data**|||
|---|---|---|---|---|
|0x0E<br>0x00<br>**0xCA**|0x00|**CANBoosterS**|**ystemState** (1|0Bytes)|
|**CANBoosterSystemSt**|**ate**ist wie fo|lgt aufgebaut (d|ie 16-bit Werte|sind little endian):|
|**Byte Offset**<br>**Typ**|**Name**||**Wert**||
|0<br>UINT16|**NId**||0xC101<br>…<br>0xC1FF|**CAN-NetworkID**des Boosters|
|2<br>UINT16|Booster_Ou|tputPort|1<br>2|Ausgang erste Endstufe<br>Ausgang zweite Endstufe (nur 10807)|
|4<br>UINT16|Booster_St|ate|bitmask|siehe unten|
|6<br>UINT16|Booster_VC|CVoltage|mV|Spannung an der Endstufe|
|8<br>UINT16|Booster_Cu|rrent|mA|Strom an der Endstufe|



### Bitmasken für **Booster_State** : 

```
#define bsBgActive
#define bsShortCircuit
#define bsTrackVoltageOff
#define bsRailComActive
```

```
0x0001 // Bremsgenerator aktiv (ZCAN SSP)
0x0020 // Kurzschluss an Endstufe (ZCAN UES)
0x0080 // Gleisspannung ist abgeschaltet (OFF)
0x0800 // RailCom-Cutout aktiv
```

**Ab Booster FW Version V1.11** (Booster Manangement) **:** 

```
#define bsOutputDisabled
```

```
0x0100 // Booster Ausgang deaktiviert (by user)
```

Dokumentenversion 1.13 

60/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **10.2.4 LAN_CAN_BOOSTER_SET_TRACKPOWER** 

Booster Management durch Anwender: CAN-Booster Gleisausgänge deaktivieren und reaktivieren. 

|Anforderung an|Z21:||||
|---|---|---|---|---|
|**DataLen**|**Header**||**Data**||
|0x07<br>0x00|**0xCB**|0x00|**NId**16 bit|**Power **8 bit|



**NId** ist die CAN-NetworkID des gewünschten Boosters (16 bit little endian, 0xC101 bis 0xC1FF). Siehe auch weiter oben **_10.2.3_** LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD. 

**Power** 0x00 … alle Booster Gleisausgänge deaktivieren 0xFF … alle Booster Gleisausgänge reaktivieren Zusätzlich **ab Z21 FW Version V1.42** und **Booster FW Version V1.11** : 0x10 … ersten Booster Gleisausgang deaktivieren 0x11 … ersten Booster Gleisausgang reaktivieren 0x20 … zweiten Booster Gleisausgang deaktivieren (Z21 dual BOOSTER) 0x22 … zweiten Booster Gleisausgang reaktivieren (Z21 dual BOOSTER) 

**Hinweis:** Booster Gleisausgänge können nur dann wieder tatsächlich eingeschaltet werden, wenn auch die Zentrale Z21 ebenfalls eingeschaltet ist und ein gültiges Gleissignal an die CAN-Booster sendet. Die Einstellungen des Booster Managements werden nicht persistent gespeichert. 

Antwort von Z21: 

Bei Änderung des CANBoosterSystemState **_10.2.3_** LAN_CAN_BOOSTER_SYSTEMSTATE_CHGD an Clients mit Abo. 

Dokumentenversion 1.13 

61/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **11 zLink** 

Die erstmals mit Z21 single BOOSTER eingeführte **zLink-Schnittstelle** erlaubt es, auch Endgeräte mit kleinerem Microcontroller ohne eigenem LAN oder WLAN Interface in sein eigenes Netzwerk zu integrieren. 

Endgeräte mit zLink Schnittstelle sind mit Stand 06/2021: 

- 10806 Z21 single BOOSTER 

- 10807 Z21 dual BOOSTER 

- 10869 Z21 XL BOOSTER 

- 10836 Z21 switch DECODER 

- 10837 Z21 signal DECODER 

### **_11.1 Adapter_** 

An die zLink Schnittstelle der oben genannten Geräte kann ein Adapter angeschlossen werden, über welchen das Endgerät mit der Außenwelt kommunizieren kann. Ein solcher Adapter ist der **10838 Z21 pro LINK** . 

### **11.1.1 10838 Z21 pro LINK** 

Der **10838 Z21 pro LINK** verbindet als **Gateway** die **zLink Schnittstelle mit dem WLAN** und kann so für folgende Aufgaben verwendet werden: 

1. **Konfiguration** des Endgeräts (per Tasten & Display, Z21 App, Z21 Maintenance Tool am PC) 

2. **Firmware Update** des Endgeräts (per Z21 Updater App, Z21 Maintenance Tool am PC) 

3. <u>Steuerung des Endgeräts durch WLAN Clients über das</u> **<u>Z21 LAN Protokoll</u>** 

Letzterer Punkt 3 war zuerst lediglich als Testschnittstelle gedacht, doch bald war klar, dass sich hier interessante Möglichkeiten in Richtung dezentraler, per WLAN vernetzter Anlagen eröffnen. Es bedeutet aus technischer Sicht, dass (mit Rücksicht auf den eingeschränkten Speicher) im jeweiligen Endgerät ein auf die Aufgaben des Endgeräts zugeschnittener **Z21 Protokoll-Stack** implementiert ist. Siehe auch _Tabelle 1 Meldungen vom Client an Z21_ und _Tabelle 2 Meldungen von Z21 an Clients._ Über das WLAN/zLink Gateway können nun - so wie an eine Zentrale – wie gewohnt Kommandos per UDP an das Endgerät geschickt werden. Zum Beispiel können die Gleisausgänge eines Boosters über das WLAN/zLink Gateway ein- und ausgeschaltet werden, oder der Booster-Systemstatus abgefragt werden. Es können über diese Schnittstelle am Z21 switch DECODER aber auch Weichen direkt geschaltet werden, bzw. ebenso beim Z21 signal DECODER Signale direkt angesteuert werden, und das sogar _ohne jegliche Verbindung zum Hauptgleis der Zentrale_ . Die Decoder können über die zLink Schnittstelle per CV-Schreibbefehle sogar konfiguriert werden. 

Es wurde versucht, dass es für den WLAN Client möglichst transparent bleibt, ob er nun mit einer Zentrale oder über das WLAN/zLink Gateway mit einem Endgerät kommuniziert. Angesichts der teilweise sehr kleinen CPU im Endgerät sollten aber folgende Punkte beachtet werden: 

- Eingeschränkte Bandbreite: die effektive Transferrate sollte insgesamt deutlich unter 1024 Bytes/s bleiben. Mehr ist bei den aktuell verfügbaren Endgeräten auch weder notwendig noch sinnvoll. 

- Geben Sie dem Endgerät genügend Zeit, die Befehle und Daten zu verarbeiten. Halten Sie daher zwischen zwei Befehlen eine Pause von mindestens 50 ms ein. 

- Z21 pro LINK vorzugsweise im Client Mode verwenden 

- Wenn möglich nur ein WLAN Client mit Z21 pro Link verbinden, maximal sind 4 Clients erlaubt 

Ein Betrieb per UPD Broadcasts ist zwar möglich, es wird aber empfohlen, dies nur zum Auffinden der Geräte im Netzwerk zu verwenden (siehe weiter unten). Danach können die Endgeräte über ihren Hardware-Typ (LAN_GET_HWINFO) und Seriennummer (LAN_GET_SERIAL_NUMBER), sowie über die 

Dokumentenversion 1.13 

62/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



IP-Adresse des jeweiligen Z21 pro LINK eindeutig zugeordnet werden. Zusätzlich kann der Benutzer in jedem Endgerät einen Namen (Freitext) hinterlegen, der ebenfalls angezeigt werden kann. 

Ein Befehl, der vom Z21 pro LINK nicht an sein Endgerät durchreicht, sondern selbst verarbeitet und beantwortet, ist LAN_ZLINK_GET_HWINFO. 

### **11.1.1.1 LAN_ZLINK_GET_HWINFO** 

Mit diesem Befehl können die Eigenschaften des Z21 pro LINK vom LAN Client abgefragt werden. 

Wenn dieses Kommando als UDP Broadcast versendet wird, dann ist es möglich anhand der Antworten die im WLAN angemeldeten Z21 pro LINK aufzufinden und über ihre MAC Adresse und zugewiesener IP Adresse zu verwalten. 

|Anforderung an Z21 pro LINK:||
|---|---|
|**DataLen**<br>**Header**|**Data**|
|0x05<br>0x00<br>**0xE8**<br>0x00|**0x06**|



Data[0] = **0x06** = ZLINK_MSG_TYPE_HW_INFO 

|Antwort von Z21|pro LINK:|||
|---|---|---|---|
|**DataLen**|**Header**||**Data**|
|0x3F<br>0x00|**0xE8**|0x00|**0x06**<br>**Z_Hw_Info**(58 Bytes)|



Data[0] = **0x06** = ZLINK_MSG_TYPE_HW_INFO 

- **<u>Z_Hw_Info</u>** <u>ist wie folgt aufgebaut (die 16 bit Werte sind little endian):</u> 

|<br>**Byte Offset**|<br>**Typ**|<br>**Name**||**Beispiel**|
|---|---|---|---|---|
|0|UINT16|**HwID**||401 (0x191)|
|2|UINT8|FW_Version_Major||1|
|3|UINT8|FW_Version_Minor||1|
|4|UINT16|FW_Version_Build||3217 (0xC91)|
|6|UINT8[18]|**MAC_Address**|string|„EC FA BC 4F 04 C6“|
|24|UINT8[33]|**Name**|string|„this_is_a_quite_long_device_name“|
|57|UINT8|Reserved|0x00|0|



### **HwID** 

### 401 = 0x191 … Adapter **10838 Z21 pro LINK** 

### **MAC_Address** 

MAC Adresse des Adapters als nullterminierte Zeichenkette, 8-bit ASCII. 

### **Name** 

Vom Anwender konfigurierbarer Name des Adapters als nullterminierte Zeichenkette. Maximal 32 Zeichen zuzüglich 0x00 Ende Kennung, Codierung 8-bit ISO 8859-1 ( _Latin-1_ ). Ignorieren Sie alle Zeichen nach dem ersten 0x00. 

Beispiel: 

**`3f 00 e8 00 06 91 ?....`** `.` **`01`** `01 01 91 0c` <u>`45 43 20 46 41 20 42 43 20 34 46`</u> `.....EC FA BC 4F` <u>`20 30 34 20 43 36 00`</u> `74 68 69 73 5f 69 73 5f 61    04 C6.this_is_a 5f 71 75 69 74 65 5f 6c 6f 6e 67 5f 64 65 76 69   _quite_long_devi 63 65 5f 6e 61 6d 65 00 00                        ce_name..` HwID: **0x191** = 401 = 10838 Z21 pro LINK FW Version: V1.1.3217 MAC Adresse: „EC FA BC 4F 04 C6“ Name: „this_is_a_quite_long_device_name” 

Dokumentenversion 1.13 

63/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_11.2 Booster 10806, 10807 und 10869_** 

Unterstützte Befehle siehe _Tabelle 1 Meldungen vom Client an Z21_ und _Tabelle 2 Meldungen von Z21 an Clients_ . Zusätzlich wurden für die Booster einige neue Befehle eingeführt, die nur für die Booster gültig sind. 

### **11.2.1 LAN_BOOSTER_GET_DESCRIPTION** 

Bezeichnung aus Booster auslesen. 

Im Booster kann vom Anwender ein Name (Freitext) hinterlegt werden, damit er das Gerät später leichter wieder identifizieren kann. 

<u>Anforderung an BOOSTER:</u> 

|<br>**DataLen**|<br>**Header**||**Data**|
|---|---|---|---|
|0x04<br>0x00|**0xB8**|0x00|-|
|Antwort von BOO|STER:|||
|**DataLen**|**Header**||**Data**|
|0x24<br>0x00|**0xB8**|0x00|UINT8**Name**[32]|



**Name** entspricht der hinterlegten Bezeichnung als nullterminierter String. Der String sollte gemäß **ISO 8859-1** ( _Latin-1_ ) codiert sein und aus Gründen der Kompatibilität zum CAN-Bus nicht länger als 16 Zeichen sein. 

**Sonderfall** : Name[0] kann 0xFF sein, falls im Gerät noch nie eine Bezeichnung abgelegt worden ist. Dieser Fall muss als Leerstring interpretiert werden. 

Beispiel: ”Test” **`24 00 b8 00 54 65 $...Te 73 74`** `00 00 00 00 00 00 00 00 00 00 00 00 00 00` **`st`** `.............. 00 00 00 00 00 00 00 00 00 00 00 00 00 00         ..............` 

### **11.2.2 LAN_BOOSTER_SET_DESCRIPTION** 

Bezeichnung im Booster überschreiben. 

<u>Anforderung an BOOSTER:</u> 

|**DataLen**|**Header**||**Data**|
|---|---|---|---|
|0x24<br>0x00|**0xB9**|0x00|UINT8**Name**[32]|



**Name** entspricht der zu hinterlegenden Bezeichnung als nullterminierter String. Der String sollte gemäß **ISO 8859-1** ( _Latin-1_ ) codiert sein und aus Gründen der Kompatibilität zum CAN-Bus nicht länger als 16 Zeichen sein. Füllen Sie den Rest von Data mit 0x00 auf. 

**Nicht erlaubte Zeichen sind das Anführungszeichen “ (0x22) und der Backslash \ (0x5C)** . 

Antwort von BOOSTER: Keine 

Dokumentenversion 1.13 

64/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **11.2.3 LAN_BOOSTER_SYSTEMSTATE_GETDATA** 

Anfordern des aktuellen Systemzustandes. 

<u>Anforderung an BOOSTER:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|0x04|0x00|**0xBB**|0x00|-|



Antwort von BOOSTER: 

Siehe unten **11.2.4** LAN_BOOSTER_SYSTEMSTATE_DATACHANGED 

### **11.2.4 LAN_BOOSTER_SYSTEMSTATE_DATACHANGED** 

Änderung des Systemzustandes vom Booster an den Client melden. 

Diese Meldung wird asynchron vom Booster an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000100 

- den Systemzustand explizit angefordert hat, siehe oben **_11.2.3_** LAN_BOOSTER_SYSTEMSTATE_GETDATA. 

### <u>BOOSTER an Client:</u> 

|**DataLen**|**Header**|**Data**|
|---|---|---|
|0x1C<br>0x00|**0xBA**<br>0x00|**BoosterSystemState**(24 Bytes)|



- **<u>BoosterSystemState</u>** <u>ist wie folgt aufgebaut (die 16 bit Werte sind little endian):</u> 

|**Byte Offset**|<br>**Typ**|<br>**Name**|||
|---|---|---|---|---|
|0|INT16|Booster_1_MainCurrent|mA|Strom an der 1. Endstufe|
|2|INT16|Booster_2_MainCurrent|mA|Strom an der 2. Endstufe|
|4|INT16|Booster_1_FilteredMainCurrent|mA|Geglätteter Strom 1. Endstufe|
|6|INT16|Booster_2_FilteredMainCurrent|mA|Geglätteter Strom 2. Endstufe|
|8|INT16|Booster_1_Temperature|°C|Temperatur der 1. Endstufe|
|10|INT16|Booster_2_Temperature|°C|Temperatur der 2. Endstufe|
|12|UINT16|SupplyVoltage|mV|Versorgungsspannung|
|14|UINT16|Booster_1_VCCVoltage|mV|Spannung an der 1. Endstufe|
|16|UINT16|Booster_2_VCCVoltage|mV|Spannung an der 2. Endstufe|
|18|UINT8|CentralState|bitmask|siehe unten|
|19|UINT8|CentralStateEx|bitmask|siehe unten|
|20|UINT8|CentralStateEx2|bitmask|siehe unten|
|21|UINT8|Reserved1|||
|22|UINT8|CentralStateEx3|bitmask|siehe unten|
|23|UINT8|Reserved2|||



### Bitmasken für **CentralState** : 

```
#define csTrackVoltageOff  0x02
#define csConfigMode 0x10
#define csCanConnected 0x20
```

```
// Die Gleisspannung ist abgeschaltet
// Konfigurationsmodus aktiv
// CAN Verbindung mit Zentrale Ok
```

Dokumentenversion 1.13 

65/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### Bitmasken für **CentralStateEx** : 

```
#define cseHighTemperature  0x01 // zu hohe Temperatur
#define csePowerLost 0x02 // zu geringe Eingangsspannung
#define cseBooster_1_ShortCircuit 0x04 // Kurzschluss an 1. Endstufe
#define cseBooster_2_ShortCircuit 0x08 // Kurzschluss an 2. Endstufe
#define cseRevPol 0x10 // Fehler Versorgungsspannung
#define cseNoDCCInput 0x80 // kein DCC-Eingangssignal vorhanden
```

### Bitmasken für **CentralStateEx2** : 

```
#define cse2Booster_1_RailComActive 0x01
#define cse2Booster_2_RailComActive 0x02
#define cse2Booster_1_MasterSettings 0x04
#define cse2Booster_2_MasterSettings 0x08
#define cse2Booster_1_BgActive   0x10
#define cse2Booster_2_BgActive 0x20
#define cse2Booster_1_RailComFwd  0x40
#define cse2Booster_2_RailComFwd  0x80
```

```
// RailCom aktiv 1. Endstufe
// RailCom aktiv 2. Endstufe
// CAN Autosettings Ok 1. Endstufe
// CAN Autosettings Ok 2. Endstufe
// Bremsgenerator aktiv 1. Endstufe
// Bremsgenerator aktiv 2. Endstufe
// RailCom Forwarding aktiv 1. Endstufe
// RailCom Forwarding aktiv 2. Endstufe
```

### Bitmasken **fürCentralStateEx3** : 

```
#define cse3Booster_1_OutputInverted 0x01 // 1. Endstufe invertiert (Autoinvert)
#define cse3Booster_2_OutputInverted 0x02 // 2. Endstufe invertiert (Autoinvert)
Ab Booster FW Version V1.11:
#define cse3Booster_1_OutputDisabled 0x10 // 1. Endstufe deaktiviert (by user)
#define cse3Booster_2_OutputDisabled 0x20 // 2. Endstufe deaktiviert (by user)
```

### **11.2.5 LAN_BOOSTER_SET_POWER** 

**Ab Booster FW Version 1.11** : Booster Management durch Anwender. 

Falls hier am Booster _alle_ Gleisausgänge deaktiviert bzw. reaktiviert werden, dann entspricht dieser Befehl defacto einem LAN_X_SET_TRACK_POWER_OFF bzw. LAN_X_SET_TRACK_POWER_ON an den Booster. Mit LAN_BOOSTER_SET_POWER ist es dagegen möglich, am 10807 Z21 dual BOOSTER auch einen _einzelnen_ Gleisausgang gezielt aus- und wieder einzuschalten. 

### <u>Anforderung an BOOSTER:</u> 

|**DataLen**|**Header**|**Data**||
|---|---|---|---|
|0x06<br>0x00|**0xB2**<br>0x00|**BoosterPort 8 bit**|**BoosterPortState 8 bit**|



### **BoosterPort** 

0x01 … ersten Booster Gleisausgang auswählen 0x02 … zweiten Booster Gleisausgang auswählen (nur Z21 dual BOOSTER) 0x03 … alle Booster Gleisausgänge auswählen 

### **BoosterPortState** 

0x00 … ausgewählte Booster Gleisausgänge deaktivieren 0x01 … ausgewählte Booster Gleisausgänge reaktivieren 

**Hinweis:** Booster Gleisausgänge können nur dann wieder tatsächlich eingeschaltet werden, wenn auch die Zentrale Z21 ebenfalls eingeschaltet ist und ein gültiges Gleissignal an die CAN-Booster sendet. Die Einstellungen des Booster Managements werden nicht persistent gespeichert. 

Antwort von BOOSTER: Bei Änderung des BoosterSystemState **11.2.4** LAN_BOOSTER_SYSTEMSTATE_DATACHANGED an Clients mit Abo. 

Dokumentenversion 1.13 

66/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_11.3 Decoder 10836 und 10837_** 

Unterstützte Befehle siehe _Tabelle 1 Meldungen vom Client an Z21_ und _Tabelle 2 Meldungen von Z21 an Clients_ . Es wurden einige neue Befehle eingeführt, die nur für die Decoder gültig sind. 

### **11.3.1 LAN_DECODER_GET_DESCRIPTION** 

Bezeichnung aus Decoder auslesen. 

Im Decoder kann vom Anwender ein Name (Freitext) abgespeichert werden, um das Gerät später leichter wieder identifizieren zu können. 

<u>Anforderung an DECODER:</u> 

|<br>**DataLen**|<br>**Header**||**Data**|
|---|---|---|---|
|0x04<br>0x00|**0xD8**|0x00|-|
|Antwort von DEC<br>|ODER:<br>|||
|**DataLen**|**Header**||**Data**|
|0x24<br>0x00|**0xD8**|0x00|UINT8**Name**[32]|



**Name** Codierung siehe 11.2.1 LAN_BOOSTER_GET_DESCRIPTION 

### **11.3.2 LAN_DECODER_SET_DESCRIPTION** 

Bezeichnung im Decoder überschreiben. 

<u>Anforderung an DECODER:</u> 

|**DataLen**|**Header**||**Data**|
|---|---|---|---|
|0x24<br>0x00|**0xD9**|0x00|UINT8 **Name**[32]|



**Name** Codierung siehe 11.2.2 LAN_BOOSTER_SET_DESCRIPTION. 

Antwort von DECODER: Keine 

### **11.3.3 LAN_DECODER_SYSTEMSTATE_GETDATA** 

Anfordern des aktuellen Systemzustandes. 

<u>Anforderung an DECODER:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|0x04|0x00|**0xDB**|0x00|-|



Antwort von DECODER: 

Siehe unten **_11.3.4_** LAN_DECODER_SYSTEMSTATE_DATACHANGED 

Dokumentenversion 1.13 

67/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **11.3.4 LAN_DECODER_SYSTEMSTATE_DATACHANGED** 

Änderung des Systemzustandes vom Decoder an den Client melden. 

Diese Meldung wird asynchron vom Decoder an den Client gemeldet, wenn dieser 

- den entsprechenden Broadcast aktiviert hat, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000100 

- den Systemzustand explizit angefordert hat, siehe _11.3.3_ LAN_DECODER_SYSTEMSTATE_GETDATA. 

Wenn sich der Signaldecoder trotz Abo per Broadcastflags nach 4 Sekunden nicht meldet, weil sich z.B. kein Signalbegriff geändert hat, dann kann bei Bedarf auch gepollt werden. 

Die Antworten von 10836 Z21 switch DECODER und 10837 Z21 signal DECODER **unterscheiden sich im Aufbau und Inhalt** und können Anhand von **DataLen** unterschieden werden. 

### **11.3.4.1 SwitchDecoderSystemState** 

### **<u>10836 Z21 switch DECODER</u>** <u>an Client:</u> 

|**DataLen**|**Header**|**Data**|
|---|---|---|
|**0x30**<br>0x00|**0xDA**<br>0x00|**SwitchDecoderSystemState**(44 Bytes)|



- **<u>SwitchDecoderSystemState</u>** <u>ist wie folgt aufgebaut (die 16 bit Werte sind little endian):</u> 

|**Byte Offset**|**Typ**|<br>**Name**|||
|---|---|---|---|---|
|0|INT16|Current|mA|Strom|
|2|INT16|**FilteredCurrent**|mA|Geglätteter Strom|
|4|UINT16|Voltage|mV|Interne Spannung (3.3V)|
|6|UINT8|**CentralState**|bitmask|siehe unten|
|7|UINT8|**CentralStateEx**|bitmask|siehe unten|
|8|UINT8[8]|**OutputStates**[0..7]||Status pro Ausgang|
|16|UINT8[8]|**OutputConfig**[0..7]||Betriebsmodus pro Ausgang|
|24|UINT8[4]|**OutputDimm**[0..7]||Dimmwert pro Ausgang|
|32|UINT16|**Address**||Erste Decoderadresse|
|34|UINT16|**Address2**||Zweite Decoderadresse|
|36|UINT8[6]|Reserved1|||
|42|UINT8|**Dimmed**||1 Bit pro Ausgang|
|43|UINT8|Reserved2|||



### **FilteredCurrent** 

Summe aus internem Stromverbrauch + Stromverbrauch an den Klemmen 

Bitmasken für **CentralState** : `#define csEmergencyStop 0x01 // Not-Aus für Decoder #define csTrackVoltageOff 0x02 // Die Gleisspannung ist abgeschaltet #define csShortCircuit 0x04 // Kurzschluss erkannt #define csConfigMode 0x10 // Konfigurationsmodus aktiv` Bitmasken für **CentralStateEx** : `#define csePowerLost 0x02 // zu geringe Eingangsspannung #define cseRCN213 0x20 // Adressierung gem. RCN213 #define cseNoDCCInput 0x80 // kein DCC-Eingangssignal vorhanden` 

Dokumentenversion 1.13 

68/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **OutputState** 

Zustand des Ausgangs `#define oUnknown 0x00 #define oRedActive 0x11 #define oRedInactive 0x01 #define oGreenActive 0x12 #define oGreenInactive 0x02` 

### **OutputConfig** 

Betriebsmodus des Ausgangs `#define ocfgNormal 0 // Impulsbetrieb (default) #define ocfgBlinker 1 // Wechselblinker #define ocfgBlinkSm 2 // Wechselblinker mit Ein- und Ausblenden #define ocfg10775 3 // Momentbetrieb wie 10775 #define ocfgK84 4 // Dauerbetrieb (zB für Beleuchtung) #define ocfgK84Sm 5 // Dauerbetrieb mit Ein- und Ausblenden` 

### **OutputDimm** 

Dimmwert 0 … Dimmung deaktiviert, entspricht daher voller Ausgangsleistung 1 bis 100 … minimal bis maximal mögliche Ausgangsleistung 

### **Address** 

Einer Decoderadresse entsprechen 4 Weichennummern. Das heißt: Erste Decoderadresse = 1 … Weichennummer 1 bis 4 Erste Decoderadresse = 2 … Weichennummer 5 bis 8 Erste Decoderadresse = 3 … Weichennummer 9 bis 12 usw. 

### **Address2** 

Zweite Decoderadresse **= 0** : zweite Decoderadresse entspricht **automatisch** „Erste Decoderadresse **+ 1** “ ansonst gilt: Zweite Decoderadresse = 1 … Weichennummer 1 bis 4 Zweite Decoderadresse = 2 … Weichennummer 5 bis 8 Zweite Decoderadresse = 3 … Weichennummer 9 bis 12 usw. 

### **Dimmed** 

1 Bit pro Ausgangspaar: 

0 … Ausgangspaar wird nicht gedimmt 

1 … Ausgangspaar wird gedimmt oder sanftes Auf-/Abblenden ist konfiguriert LSB = Ausgangspaar 1; MSB = Ausgangspaar 8 

Dokumentenversion 1.13 

69/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **11.3.4.2 SignalDecoderSystemState** 

### **<u>10837 Z21 signal DECODER</u>** <u>an Client:</u> 

|**DataLen**|**Header**|**Data**|
|---|---|---|
|**0x2E**<br>0x00|**0xDA**<br>0x00|**SignalDecoderSystemState**(42 Bytes)|



|**SignalDecod**<br>|**erSystemSta**<br>|**te**ist wie folgt aufgebaut<br>|(die 16-bit Wer|te sind little endian):|
|---|---|---|---|---|
|**Byte Offset**|**Typ**|**Name**|||
|0|INT16|Current|mA|0 / Reserviert|
|2|INT16|FilteredCurrent|mA|0 / Reserviert|
|4|UINT16|**Voltage**|mV|Spannung an den Klemmen|
|6|UINT8|**CentralState**|bitmask|siehe unten|
|7|UINT8|**CentralStateEx**|bitmask|siehe unten|
|8|UINT8[2]|**OutputStates**[0..1]||Ein/Aus-Status für Ausgänge A1…B8|
|10|UINT8[2]|**BlinkStates**[0..1]||Blink-Status für Ausgänge A1…B8|
|12|UINT8[4]|**SignalDccExt**[0..3]|DCCext|Aktueller Signalbegriff 1. bis 4. Signal|
|16|UINT8[4]|SignalCurrAsp[0..3]|Index|Aktueller Signalbegriff 1. bis 4. Signal|
|20|UINT8[3]|Reserved1|||
|23|UINT8|**SignalCount**|2, 3, 4|Anzahl der verwendeten Signale|
|24|UINT8[4]|**SignalConfig**[0..3]|Signal-ID|Signalkonfiguration 1. bis 4. Signal|
|28|UINT8[4]|SignalInitAsp[0..3]|Index|Initialisierung 1. bis 4. Signal|
|32|UINT16|**Address**||Erste Decoderadresse|
|34|UINT16[4]|Reserved2|||



### Bitmasken für **CentralState** : 

`#define csEmergencyStop 0x01 // Not-Aus für Decoder #define csTrackVoltageOff 0x02 // Die Gleisspannung ist abgeschaltet #define csShortCircuit 0x04 // Kurzschluss erkannt #define csConfigMode 0x10 // Konfigurationsmodus aktiv` Bitmasken für **CentralStateEx** : `#define csePowerLost 0x02 // zu geringe Eingangsspannung #define cseEEPromError 0x10 // EEPROM Schreib/Lesefehler #define cseRCN213 0x20 // Adressierung gem. RCN213 #define cseNoDCCInput 0x80 // kein DCC-Eingangssignal vorhanden` 

### **OutputStates** 

OutputStates[0]: LSB = Ausgang A1; MSB = Ausgang A8 OutputStates[1]: LSB = Ausgang B1; MSB = Ausgang B8 

### **BlinkStates** 

BlinkStates[0]: LSB = Ausgang A1; MSB = Ausgang A8 BlinkStates[1]: LSB = Ausgang B1; MSB = Ausgang B8 

### **SignalDccExt** und **SignalConfig** 

SignalConfig definiert als **Signal-ID** eindeutig den Signaltyp. SignalDccExt definiert als **DCCext** -Wert den aktuellen Signalbegriff zur gegeben Signal-ID. Werte für Signal-ID und DCCext siehe <u>https://www.z21.eu/de/produkte/z21-signal-decoder/signaltypen.</u> 

### **Address** 

Einer Decoderadresse entsprechen 4 Signaladressen. Der Signaldecoder belegt 4 Decoderadressen hintereinander und somit 4x4=16 Signaladressen. Erste Decoderadresse = 1 … Signaldecoder belegt Signaladressen 1 bis 16 Erste Decoderadresse = 2 … Signaldecoder belegt Signaladressen 5 bis 20 Erste Decoderadresse = 3 … Signaldecoder belegt Signaladressen 9 bis 24 usw. 

Dokumentenversion 1.13 

70/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **12 Modellzeit** 

### **Ab Z21 FW Version 1.43.** 

Mit Firmware Version 1.43 wurden die Möglichkeiten der bereits bestehenden LocoNet Fastclock stark erweitert, sodass nun die beschleunigte Modellzeit der Z21 auch den Teilnehmern am Gleis, X-BUS und LAN zur Verfügung steht. Die Modellzeit kann vom Anwender bis zum Faktor ≤ 63 beschleunigt werden. Das erlaubt dem fortgeschrittenen Anwender dann ein Fahren nach Fahrplan, trotz verkürzter Streckenlängen zwischen den Modellbahnstationen. 

Die Z21 besitzt allerdings keine Echtzeituhr, die nach dem Abschalten der Zentrale weiterlaufen würde. Daher beginnt die Modellzeit immer bei der gleichen, durch den Anwender einstellbaren Startzeit. Das Verhalten beim Nothalt und Kurzschluss, sowie die Ausgabe auf Gleis, LocoNet, X-BUS und IP Multicast sind ebenfalls vom Anwender konfigurierbar. 

- DCC-Zeitmeldungen am Gleis siehe RCN-211. 

- Bei LocoNet kann vom Endgerät etwa alle 70 bis 100 Sekunden der sogenannte Clock Slot 0x7B gepollt werden. Siehe auch LocoNet Spec (z.B. personal edition zu Lernzwecken). 

- Am X-BUS erfolgt die Zeitmeldung gemäß XpressNet™ V4.0 einmal pro Modellminute. 

- Auf der LAN Schnittstelle kann die Modellzeit optional auch per „MRclock“ Multicast versendet werden. Das erlaubt die Verwendung von MRclock Clients wie zum Beispiel die Android MRclock App zur Anzeige der Modellzeit. Falls aktiviert, wird der MRclock Multicast dann einmal pro Modellminute (aber mindestens dreimal pro echter Minute) an die Adresse 239.50.50.20, Port 2000 versendet. 

Zusätzlich gibt es auch Z21 LAN Befehle für die Modellzeit, die nun wie folgt beschrieben werden. 

### **_12.1 LAN_FAST_CLOCK_CONTROL_** 

### **12.1.1 Modellzeit lesen** 

Mit folgendem Befehl kann die aktuelle Modellzeit ausgelesen werden. 

|Anforderung an|Z21:|||||
|---|---|---|---|---|---|
|**DataLen**|**Header**||**Data**|||
|0x07<br>0x00|**0xCC**|0x00|0x21|0x2A|0x0B|



Antwort von Z21: Siehe unten **_12.2_** LAN_FAST_CLOCK_DATA. 

### **12.1.2 Modellzeit setzen** 

Mit folgendem Befehl kann die Rate und die aktuelle Modellzeit auf eine gewünschte Zeit gesetzt werden. 

|Anforderung an<br>**DataLen**|Z21:<br>**Header**||**Data**||||||
|---|---|---|---|---|---|---|---|---|
|0x0A<br>0x00|**0xCC**|0x00|0x24|0x2B|DDDhhhhh|00mmmmmm|00rrrrrr|XOR-Byte|



Dokumentenversion 1.13 

71/78 

06.11.2023 

|Z21 LAN Protokoll Spezifikation|
|---|





**DDD** Der gewünschte Modellzeit-Wochentag in 3 Bits. Wertebereich von 0 = Montag bis 6 = Sonntag. **hhhhh** Die gewünschte Modellzeit-Stunde in 5 Bits, Wertebereich 0 bis 23. **mmmmmm** Die gewünschte Modellzeit-Minute in 6 Bits, Wertebereich 0 bis 59. **rrrrrr** Die gewünschte Modellzeit-Rate (Beschleunigungsfaktor) in 6 Bits. Wertebereich  von 0 bis 63: (0 … Modellzeit bleibt stehen. Nicht empfohlen, besser ist: **_12.1.4_** Modellzeit anhalten) 1 … Echtzeit 2 … Modellzeit läuft doppelt so schnell 3 … Modellzeit läuft dreimal so schnell usw. **Hinweis:** Die Rate wird in der Z21 persistent gespeichert. XOR-Byte XOR Prüfsumme über Data Antwort von Z21: **_12.2_** LAN_FAST_CLOCK_DATA an Clients mit Abo. 

### **12.1.3 Modellzeit starten** 

Mit folgendem Befehl kann die Modellzeituhr gestartet (d.h. fortgesetzt) werden. 

|Anforderung an Z|21:||
|---|---|---|
|**DataLen**|**Header**<br>**Data**||
|0x07<br>0x00|**0xCC**<br>0x00<br>0x21<br>0x2C|0x0D|
|Antwort von Z21:|||
|**_12.2_**LAN_FAST_|CLOCK_DATA an Clients mit Abo.||



**Hinweis:** Der geänderte Zustand „fcFastClockEnabled“ wird in der Z21 persistent gespeichert. 

### **12.1.4 Modellzeit anhalten** 

Mit folgendem Befehl kann die Modellzeituhr angehalten werden. 

|Anforderung an|Z21:|||||
|---|---|---|---|---|---|
|**DataLen**|**Header**||**Data**|||
|0x07<br>0x00|**0xCC**|0x00|0x21|0x2D|0x0C|



Antwort von Z21: **_12.2_** LAN_FAST_CLOCK_DATA an Clients mit Abo. 

**Hinweis:** Der der geänderte Zustand „not fcFastClockEnabled“ wird in der Z21 persistent gespeichert. 

Dokumentenversion 1.13 

72/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_12.2 LAN_FAST_CLOCK_DATA_** 

Aktuelle Modellzeit an Clients melden. Diese Meldung wird asynchron von der Z21 an die Clients gemeldet, wenn diese 

- den entsprechenden Broadcast aktiviert haben, siehe **_2.16_** LAN_SET_BROADCASTFLAGS _,_ Flag 0x00000010, oder 

- die Modellzeit explizit angefordert haben, siehe oben **_12.1.1_** Modellzeit lesen. 

Diese Meldung wird bei laufender Modellzeituhr asynchron von der Z21 ca. einmal pro Modellminute an die Clients mit Abo gemeldet, aber auch wenn die Modellzeit gestartet, angehalten oder neu gesetzt wird. 

Die Zentrale darf Zeitmeldungen auch auslassen, z.B. wenn sie nicht im Normalbetrieb läuft. Übersprungene Zeitmeldungen müssen von den Clients toleriert werden und können ggf. anhand des Beschleunigungsfaktors aus der letzten Zeitmeldung von den Clients selbst weiter berechnet werden. 

### <u>Z21 an Client:</u> 

|**DataLen**<br>**Head**|**er**<br>**Data**|||
|---|---|---|---|
|0x0C<br>0x00<br>**0xC**<br>**FastClockTime**ist wie<br> <br>|**D**<br>0x00<br>**FastClock**<br>folgt aufgebaut:<br>|**Time**(8 Bytes)<br>||
|**Byte Offset**<br>**Typ**|**Name**|**Wert**||
|0<br>UINT8||0x66||
|1<br>UINT8||0x25||
|2<br>UINT8|**DDDh hhhh**||Modellzeit Wochentag und Stunde|
|3<br>UINT8|00**mm mmmm**||Modellzeit Minute|
|4<br>UINT8|**SH**ss ssss||Modellzeit Sekunde,<br>mit STOP-und HALT-Flag|
|5<br>UINT8|00**rr rrrr**||Modellzeit Rate|
|6<br>UINT8|**FcSettings**||Modellzeit Einstellungen Flags|
|7<br>UINT8|XOR-Byte||XOR Prüfsumme über Data|



**DDD** Der aktuelle Modellzeit-Wochentag in 3 Bits. Wertebereich 0 = Montag bis 6 = Sonntag. **hhhhh** Die aktuelle Modellzeit-Stunde in 5 Bits, Wertebereich 0 bis 23. **mmmmmm** Die aktuelle Modellzeit-Minute in 6 Bits, Wertebereich 0 bis 59. **S STOP-Flag:** die Modellzeit läuft nicht. Ursache kann sein, dass die Fastclock nicht enabled ist, oder die Rate = 0 ist, etc. **H HALT-Flag:** die Modellzeit wurde vorübergehend angehalten. Ursache kann ein Nothalt oder ein Kurzschluss am Gleis sein. **ssssss** Die aktuelle Modellzeit-Sekunde in 6 Bits, Wertebereich 0 bis 59. **rrrrrr** Die aktuelle Modellzeit-Rate (Beschleunigungsfaktor) in 6 Bits, Wertebereich 0 bis 63: (0 … Modellzeit kann nicht laufen) 1 … Echtzeit 2 … Modellzeit läuft doppelt so schnell 3 … Modellzeit läuft dreimal so schnell usw. **FcSettings** Die aktuellen persistenten Modellzeit-Einstellungen Flags, bitcodiert. Bedeutung siehe **_12.3_** LAN_FAST_CLOCK_SETTINGS_GET. 

Dokumentenversion 1.13 

73/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_12.3 LAN_FAST_CLOCK_SETTINGS_GET_** 

Mit folgendem Befehl können die persistenten Modellzeit-Einstellungen ausgelesen werden. 

|Anforde|rung an|Z21:||||||
|---|---|---|---|---|---|---|---|
|**DataLe**|**n**|**Header**||**Data**||||
|0x05|0x00|**0xCE**|0x00|0x04||||
|Antwort|von Z21|:||||||
|**DataLe**|**n**|**Header**||**Data**||||
|0x08|0x00|**0xCE**|0x00|**FcSettings**|**Rate**|**StartDDDhhhhh**|**StartMMMMMM**|



Die einzelnen Parameter in Data sind jeweils 8 bit breit. 

|**FcSettings**|Die Modellzeit-Einstellungen Flags, bitcodiert, siehe unten.|
|---|---|
|**Rate**|Die gewünschte Modellzeit-Rate (Beschleunigungsfaktor).<br>Wertebereich  von 0 bis 63:<br>(0 … Modellzeit kann nicht laufen, nicht empfohlen)<br>1 … Echtzeit<br>2 … Modellzeit läuft doppelt so schnell<br>3 … Modellzeit läuft dreimal so schnell<br>usw.|
|**StartDDDhhhhh**|Default-Startzeit Wochentag und Stunde beim Einschalten der Zentrale.<br>DDD ist der Wochentag in 3 Bits. Wertebereich 0 = Montag bis 6 = Sonntag.<br>hhhhh ist die Stunde in 5 Bits, Wertebereich 0 bis 23.|
|**StartMMMMMM**|Default-Startzeit Minute beim Einschalten der Zentrale.<br>MMMMMM ist die Minute in 6 Bits, Wertebereich 0 bis 59|



|Bitmasken für**FcSettings**:||
|---|---|
|`#define fcFastClockLocoNetEn`<br>`0x01`|`// Ausgabe am LocoNet (polled) aktivieren`|
|`#define fcFastClockXBUSEn`<br>`0x02`|`// Broadcast am XBUS aktivieren`|
|`//`<br>`0x04`|`// reserved`|
|`#define fcFastClockDCCEn`<br>`0x08`|`// DCC Broadcast am Gleis aktivieren`|
|`#define fcFastClockMRclockEn`<br>`0x10`|`// Multicast an MRclock clients aktivieren`|
|`//`<br>`0x20`|`// reserved`|
|`#define fcFastClockEmergenyHaltEn`<br>`0x40`|`// Modellzeit beim Nothalt autom. anhalten`|
|`#define fcFastClockEnabled`<br>`0x80`|`// Fastclock ist aktiviert`|



Alle hier als „reserved“ deklarierten Bits sind für zukünftige Erweiterungen reserviert und sollen weder ausgewertet noch verändert werden. 

Das Flag **`fcFastClockEmergenyHaltEn`** bewirkt, dass während eines Nothalts oder Kurzschlusses die Modellzeit automatisch pausiert wird. 

Das Flag **`fcFastClockEnabled`** ist _das_ „Enable-Flag“ für die Modellzeit. Es wird so wie **Rate** aber nicht nur über den weiter unten beschriebenen Befehl LAN_FAST_CLOCK_SETTINGS_SET verändert, sondern indirekt auch über LAN_FAST_CLOCK_CONTROL durch das Starten oder Anhalten der Modellzeit. 

Die **Werkseinstellung** ist für FcSettings=0x4F, Rate=1, StartDDDhhhhh=0 und StartMMMMMM=0. 

Dokumentenversion 1.13 

74/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_12.4 LAN_FAST_CLOCK_SETTINGS_SET_** 

Mit folgenden Befehlen können die persistenten Modellzeit-Einstellungen gezielt überschrieben werden. Die einzelnen Parameter in Data sind jeweils 8 bit breit. 

### <u>Anforderung an Z21:</u> 

|**DataLen**||**Header**||**Data**|
|---|---|---|---|---|
|0x05|0x00|**0xCF**|0x00|**FcSettings**|



Damit werden nur die Fastclock-Einstellungen **FcSettings** überschrieben. 

|Anforderung an|Z21:||||
|---|---|---|---|---|
|**DataLen**|**Header**||**Data**||
|0x06<br>0x00|**0xCF**|0x00|**FcSettings**|**Rate**|



Damit werden nur die Fastclock-Einstellungen **FcSettings** und die **Rate** überschrieben. 

|Anforderung an|Z21:||||||
|---|---|---|---|---|---|---|
|**DataLen**|**Header**||**Data**||||
|0x08<br>0x00|**0xCF**|0x00|**FcSettings**|**Rate**|**StartDDDhhhhh**|**StartMMMMMM**|



Damit werden die Fastclock-Einstellungen **_FcSettings_** , die **Rate** sowie die **Default-Startzeit** überschrieben. Die Default-Startzeit ist jene Uhrzeit, die beim Einschalten der Zentrale übernommen wird. 

Beschreibung der einzelnen Felder siehe oben **_12.3_** LAN_FAST_CLOCK_SETTINGS_GET. 

Antwort von Z21: Keine. 

Dokumentenversion 1.13 

75/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **Anhang A – Befehlsübersicht** 

### **_Client an Z21_** 

Diese Meldungen können von einem Client an eine Z21 oder an ein zLink-Gerät gesendet werden. 

|**Heade**|**r**<br>**Daten**<br>**Name**<br> <br> <br>|**L**<br>|**AN**<br>|**z**<br>|**Link**<br>|
|---|---|---|---|---|---|
||X-Header<br>DB0<br>Parameter|**Z21**<br>**Z21 XL**|**z21**<br>**z21start**|**Booster**<br>**10806**<br>**10807**|**Decoder**<br>**10836**<br>**10837**|
|||||**10869**||
|0x10|-<br>LAN_GET_SERIAL_NUMBER|✓<br>|✓<br>|✓|✓|
|0x18<br>0x1A|-<br>LAN_GET_CODE<br>-<br>LANGETHWINFO|✓<br>✓|✓<br>✓|<br>✓|<br>✓|
|0x30|__<br>-<br>LAN_LOGOFF|✓|✓|✓|✓|
|0x40|0x21<br>0x21<br>-<br>LAN_X_GET_VERSION|✓<br>|✓<br>|✓<br>|✓<br>|
|0x40|0x21<br>0x24<br>-<br>LAN_X_GET_STATUS<br>|✓<br>|✓<br>|✓<br>|✓<br>|
|0x40|0x21<br>0x80<br>-<br>LANXSETTRACKPOWEROFF|✓|✓|✓|✓|
|0x40|_____<br>0x21<br>0x81<br>-<br>LAN_X_SET_TRACK_POWER_ON|✓|✓|✓|✓ (4)|
|0x40|0x22<br>0x11<br>Register<br>LANXDCCREADREGISTER|✓|✓|||
||<br>____<br><br> <br><br>|✓|✓||✓|
|0x40<br>0x40|0x23<br>0x11<br>CV-Adresse<br>LAN_X_CV_READ<br>0x23<br>0x12<br>Register,Wert<br>LANXDCCWRITEREGISTER|✓|✓|||
|0x40|____<br>0x24<br>0x12<br>CV-Adresse, Wert<br>LAN_X_CV_WRITE|✓|✓||✓|
|0x40<br>|0x24<br>0xFF<br>Register,Wert<br>LAN_X_MM_WRITE_BYTE<br><br><br>|✓<br>|✓<br>||<br>|
|0x40|0x43<br>Weichen-Adresse<br>LAN_X_GET_TURNOUT_INFO|✓|✓||✓|
|0x40<br>|0x44<br>Zubehördecoder-Adresse<br>LAN_X_GET_EXT_ACCESSORY_INFO<br><br> <br>|✓<br>|✓<br>|<br>|✓(3)<br>|
|0x40|0x53<br>Weichen-Adresse, Schaltbefehl<br>LAN_X_SET_TURNOUT|✓|✓ (1)||✓|
|0x40<br>|0x54<br>Zubehördecoder-Adresse,Zustand<br>LAN_X_SET_EXT_ACCESSORY<br> <br>|✓<br>|✓ (1)<br>|<br>|✓<br>|
|0x40|0x80<br>-<br>LAN_X_SET_STOP|✓|✓||✓(5)|
|0x40|0x92<br>Lok-Adresse<br>LANXSETLOCOESTOP|✓|✓|||
|0x40|<br><br>_____ <br>0xE3<br>0x44<br>Lok-Adresse<br>LAN_X_PURGE_LOCO|✓|✓|||
|0x40<br>|0xE3<br>0xF0<br>Lok-Adresse<br>LAN_X_GET_LOCO_INFO<br> <br><br><br>|✓<br>|✓<br>|<br>|<br>|
|0x40|0xE4<br>0x1s<br>Lok-Adresse,Geschwindigkeit<br>LAN_X_SET_LOCO_DRIVE|✓|✓ (1)|||
|0x40<br>|0xE4<br>0xF8<br>Lok-Adresse,Funktion<br>LAN_X_SET_LOCO_FUNCTION<br> <br> <br> <br>|✓<br>|✓ (1)<br>|||
|0x40|0xE4<br>Group<br>Lok-Adresse, Funktionsgruppe<br>LAN_X_SET_LOCO_FUNCTION_GROUP|✓|✓(1)|||
|0x40|<br> <br> <br>0xE5<br>0x5F<br>Lok-Adresse,Binärzustand<br>LAN_X_SET_LOCO_BINARY_STATE|✓<br>|<br>✓<br>||<br>|
|0x40|0xE6<br>0x30<br>POM-Param, Option0xEC<br>LAN_X_CV_POM_WRITE_BYTE|✓|✓||✓|
|0x40|0xE6<br>0x30<br>POM-Param, Option 0xE8<br>LAN_X_CV_POM_WRITE_BIT|✓<br>|✓<br>||<br>|
|0x40|0xE6<br>0x30<br>POM-Param, Option0xE4<br>LANXCVPOMREADBYTE|✓|✓||✓|
|0x40|_____<br>0xE6<br>0x31<br>POM-Param, Option0xEC<br>LAN_X_CV_POM_ACCESSORY_WRITE_BYTE|✓|✓||✓|
|0x40|0xE6<br>0x31<br>POM-Param, Option 0xE8<br>LANXCVPOM ACCESSORYWRITEBIT|✓|✓|||
|0x40|<br>____ __<br>0xE6<br>0x31<br>POM-Param, Option0xE4<br>LAN_X_CV_POM_ACCESSORY_READ_BYTE|✓|✓||✓|
|0x40|0xF1<br>0x0A<br>-<br>LANXGETFIRMWAREVERSION|✓|✓|✓|✓|
|0x50|<br> <br> <br>____ <br>Broadcast-Flags<br>LAN_SET_BROADCASTFLAGS|✓|✓|✓|✓|
|0x51|-<br>LANGETBROADCASTFLAGS|✓|✓|✓|✓|
|<br>0x60|<br>__<br>Lok-Adresse<br>LAN_GET_LOCOMODE|✓|✓|||
|0x61<br>|Lok-Adresse, Modus<br>LAN_SET_LOCOMODE<br><br>|✓<br>|✓<br>|<br>|<br>|
|0x70|Funktionsdecoder-Adresse<br>LAN_GET_TURNOUTMODE|✓|✓|||
|0x71|Funktionsdecoder-AdresseModus<br>LANSETTURNOUTMODE|✓|✓|||
|<br>0x81|, <br>__ <br>Gruppenindex<br>LAN_RMBUS_GETDATA|✓|✓|||
|0x82<br>|Adresse<br>LAN_RMBUS_PROGRAMMODULE<br>|✓<br>|✓<br>|<br>|<br>|
|0x85|-<br>LAN_SYSTEMSTATE_GETDATA|✓|✓|||
|0x89<br>|Adresse<br>LAN_RAILCOM_GETDATA<br><br>|✓<br>|✓<br>|✓||
|0xA2|LocoNet-Meldung<br>LAN_LOCONET_FROM_LAN|✓|✓ (1)(2)|||
|0xA3<br>|Lok-Adresse<br>LAN_LOCONET_DISPATCH_ADDR<br> <br>|✓<br>|<br>|||
|0xA4<br>0C4|Typ, Reportadresse<br>LAN_LOCONET_DETECTOR<br>TNId<br>LANCANDETECTOR|✓<br>✓|✓(2)<br>|<br>|<br>|
|x <br>0xC8|yp, <br>__ <br>NetID<br>LAN_CAN_DEVICE_GET_DESCRIPTION|✓||||
|0xC9<br>|<br>NetID, Name<br>LAN_CAN_DEVICE_SET_DESCRIPTION<br><br>|✓<br>||||
|0xCB|NetID,PowerState<br>LANCANBOOSTERSETTRACKPOWER|✓||||
|CC|____<br>Flk S/S/G/S C<br>LANFASTCLOCKCONTROL|✓|✓|||
|0x<br>0xCE|astcoc tarttopetet ommand<br>___<br>Len<br>LANFASTCLOCKSETTINGSGET|✓|✓|||
|<br>0xCF|<br>____<br>FastclockSettings<br>LAN_FAST_CLOCK_SETTINGS_SET|✓|✓|||
|0xB2<br>|BoosterPort, BoosterPowerState<br>LAN_BOOSTER_SET_POWER<br>|<br>|<br>|✓<br>✓|<br>|
|0xB8<br>0xB9|-<br>LAN_BOOSTER_GET_DESCRIPTION<br>String<br>LANBOOSTERSETDESCRIPTION|<br>|<br>|✓|<br>|
|0xBB|___<br>-<br>LAN_BOOSTER_SYSTEMSTATE_GETDATA|||✓||
|0xD8|-<br>LANDECODERGETDESCRIPTION||||✓|
|<br>0xD9<br>0xDB|___<br>String<br>LAN_DECODER_SET_DESCRIPTION<br>-<br>LANDECODERSYSTEMSTATEGETDATA|<br>|<br>|<br>|✓<br>✓|
|<br>0xE8|___<br>0x06<br>-<br>LAN_ZLINK_GET_HWINFO|||✓(6)|✓(6)|



### **Tabelle 1 Meldungen vom Client an Z21** 

- (1) z21start: nur mit Freischaltcode (Artikelnummer 10814 oder 10818) 

- (2) z21, z21start: virtueller LocoNet-Stack (z.B. bei GBM16XN mit XPN-Interface) 

- (3) ab Decoder FW V1.11 

- (4) Decoder: Signallampen wieder einschalten (nur 10837) 

- (5) Decoder: zeigt Haltebegriff, wenn in CV38 das zweite Bit (0x02) gesetzt ist (nur 10837) 

- (6) Wird vom 10838 Z21 pro LINK beantwortet, nicht vom Endgerät (Booster oder Decoder) 

Dokumentenversion 1.13 

76/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



### **_Z21 an Client_** 

Diese Meldungen können von einer Z21 oder von einem zLink-Gerät an einen Client gesendet werden. 

|**Heade**|**r**<br>**Daten**|**Name**|**L**|**AN**|**z**|**Link**|
|---|---|---|---|---|---|---|
||X-Header<br>DB0<br>Daten||**Z21**<br>**Z21 XL**|**z21**<br>**z21start**|**Booster**<br>**10806**<br>**10807**<br>**10869**|**Decoder**<br>**10836**<br>**10837**|
|0x10|Serialnumber|Antwort auf LAN_GET_SERIAL_NUMBER|✓|✓|✓|✓|
|0x18|Code|Antwort auf LANGETCODE|✓|✓|||
|0x1A|HWType, FW Version (BCD)|__<br>Antwort auf LANGETHWINFO|✓|✓|✓|✓|
|0x40|<br>0x43<br>Weichen-Information|__<br>LANXTURNOUTINFO|✓|✓(1)||✓|
|0x40|0x44<br>Zubehördecoder-Information|___<br>LAN_X_EXT_ACCESSORY_INFO|✓|<br>✓ (1)||✓ (3)|
|0x40|0x61<br>0x00<br>-|LANXBCTRACKPOWEROFF|✓|✓|✓||
|0x40|0x61<br>0x01<br>-|_____<br>LANXBCTRACKPOWERON|✓|✓|✓||
|0x40|0x61<br>0x02<br>-|_____<br>LANXBCPROGRAMMINGMODE|✓|✓|||
|0x40|0x61<br>0x08<br>-|____<br>LAN_X_BC_TRACK_SHORT_CIRCUIT|✓|✓| (4)| (4)|
|0x40|0x61<br>0x12<br>-|LANXCVNACKSC|✓|✓|||
|0x40|0x61<br>0x13<br>-|____<br>LAN_X_CV_NACK|✓|✓||✓|
|0x40|0x61<br>0x82<br>-|LAN_X_UNKNOWN_COMMAND|✓|✓|✓|✓|
|0x40|0x62<br>0x22<br>Status|LAN_X_STATUS_CHANGED|✓|✓|✓|✓|
|0x40|0x63<br>0x21<br>XBusVersion,ID|Antwort auf LANXGETVERSION|✓|✓|✓|✓|
|0x40|0x64<br>0x14<br>CV-Result|___<br>LANXCVRESULT|✓|✓||✓|
|0x40|0x81<br>-|___<br>LAN_X_BC_STOPPED|✓|✓|||
|0x40|0xEF<br>Lok-Information|LAN_X_LOCO_INFO|✓|✓ (1)|||
|0x40|0xF3<br>0x0A<br>Version (BCD)|Antwort auf LANXGETFIRMWAREVERSION|✓|✓|✓|✓|
|0x51|<br>Broadcast-Flags|____<br>Antwort auf LAN_GET_BROADCASTFLAGS|✓|✓|✓|✓|
|0x60|<br>Lok-Adresse,Modus|<br>Antwort auf LAN_GET_LOCOMODE|✓|✓|||
|0x70|Funktionsdecoder-Adresse, Modus|Antwort auf LAN_GET_TURNOUTMODE|✓|✓|||
|0x80|Gruppenindex, Rückmelder-Status|<br>LANRMBUSDATACHANGED|✓|✓|||
|0x84|<br>SystemState|__<br>LANSYSTEMSTATEDATACHANGED|✓|✓|||
|0x88|RailCom Daten|__<br>LANRAILCOMDATACHANGED|✓|✓|✓||
|0xA0|LocoNet-Meldung|__<br>LAN_LOCONET_Z21_RX|✓||||
|0xA1|<br>LocoNet-Meldung|<br>LANLOCONETZ21TX|✓|✓ (2)|||
|0xA2|LocoNet-Meldung|___<br>LAN_LOCONET_FROM_LAN|✓|✓(2)|||
|0xA3|<br>Lok-Adresse, Ergebnis|LAN_LOCONET_DISPATCH_ADDR|✓|<br>|||
|0xA4|<br>Typ,Rückmelderadresse,Info|LAN_LOCONET_DETECTOR|✓|✓ (2)|||
|0xC4|Belegtmeldung|LANCANDETECTOR|✓||||
|0xC8|<br>NetID, Name|__<br>Antwort LANCANDEVICEGETDESCRIPTION|✓||||
|0xCA|<br>CANBoosterSystemState|____<br>LANCANBOOSTERSYSTEMSTATECHGD|✓||||
|0xCD|Fastclock Time|____<br>LANFASTCLOCKDATA|✓|✓|||
|0xCE|Fastclock Settings|___<br>LANFASTCLOCKSETTINGSGET|✓|✓|||
|0xB8|<br>String|____<br>Antwort auf LANBOOSTERGETDESCRIPTION|||✓||
|0xBA|BoosterSystemState|___<br>LANBOOSTERSYSTEMSTATEDATACHANGED|||✓||
|0xD8|<br>String|___<br>Antwort auf LANDECODERGETDESCRIPTION||||✓|
|0xDA|<br>DecoderSystemState|___<br>LAN_DECODER_SYSTEMSTATE_DATACHANGED||||✓|
|0xE8|0x06<br>Z_Hw_Info|Antwort auf LAN_ZLINK_GET_HWINFO|||✓ (5)|✓ (5)|



### **Tabelle 2 Meldungen von Z21 an Clients** 

- (1) z21start: vollfunktionsfähig nur mit Freischaltcode (Artikelnummer 10814 oder 10818) 

- (2) z21, z21start: virtueller LocoNet-Stack (z.B. bei GBM16XN mit XPN-Interface) 

- (3) ab Decoder FW V1.11 

- (4) Kurzschluss wird im entsprechenden Booster/Decoder-SystemState gemeldet 

- (5) Wird vom 10838 Z21 pro LINK beantwortet, nicht vom Endgerät (Booster oder Decoder) 

Dokumentenversion 1.13 

77/78 

06.11.2023 

Z21 LAN Protokoll Spezifikation 



## **Abbildungsverzeichnis** 

|Abbildung 1 Beispiel Sequenz Kommunikation ............................................................................................ 8|
|---|
|Abbildung 2 Beispiel Sequenz Lok-Steuerung ........................................................................................... 23|
|Abbildung 3 DCC Sniff am Gleis bei Q=0 .................................................................................................. 32|
|Abbildung 4 DCC Sniff am Gleis bei Q=1 .................................................................................................. 33|
|Abbildung 5 Beispiel Sequenz Weiche schalten ........................................................................................ 34|
|Abbildung 6 Beispiel Sequenz CV Lesen ................................................................................................... 38|
|Abbildung 7 Beispiel Sequenz Rückmeldemodul programmieren ............................................................. 46|
|Abbildung 8 Beispiel Sequenz Ethernet/LocoNet Gateway ....................................................................... 49|
|Abbildung 9 Beispiel Sequenz LocoNet Dispatch per LAN-Client ............................................................. 52|



## **Tabellenverzeichnis** 

|Tabelle 1 Meldungen vom Client an Z21 .................................................................................................... 76|
|---|
|Tabelle 2 Meldungen von Z21 an Clients ................................................................................................... 77|



Dokumentenversion 1.13 

78/78 

06.11.2023 

