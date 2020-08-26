import sys
import bs4
import requests
import numpy as np
import pandas as pd
import MySQLdb as mdb
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Arayüz Tasarımı

class Arayuz(QWidget):

    def __init__(self):
        super().__init__()
        self.top = 200
        self.left = 500
        self.width = 400
        self.height = 300
        self.setGeometry(self.left, self.top, self.width, self.height)
        ###
        self.GUI()

    def GUI(self):
        #Widgetlar

        self.baslik_label = QLabel(" ")
        self.baslik_label.setPixmap(QPixmap("Frame.png").scaled(600,200,Qt.IgnoreAspectRatio)) # Fiyat Analizi

        self.urun_label = QLabel("Ürün Seçiniz: ")
        self.urun_combo = QComboBox()
        self.urun_combo.addItems(["Çadır","Termos","Outdoor Ayakkabı","Polar Kazak"])
        self.urun_combo.currentIndexChanged.connect(self.Temizle) # Combobox indexi değişince veritabanındaki tabloyu temizler.
        self.goster_button = QPushButton("Göster")
        self.goster_button.pressed.connect(self.Sonuc_Goster)

        self.fiyat_label = QLabel("Ürün Fiyatını Giriniz: ")
        self.fiyat_lineedit = QLineEdit()
        self.fiyat_lineedit.setPlaceholderText("Girdikten Sonra Entera Basınız")
        self.fiyat_lineedit.returnPressed.connect(self.Fiyat_Hesapla) # Entera basınca fiyat karşılaştırması yapılır

        self.tahmin_label = QLabel("Ürünün, Sitelerin En Çok Satanlar\nBölümündeki Ortalama Fiyatı: ")
        self.tahmin_sonuc = QLabel("")  # Göster butonuna basınca değişir
        self.fiyat_sonuc_label = QLabel("")  # Fiyat yazıp entera basınca değişir


        #Layout

        self.layout = QGridLayout()
        self.layout.addWidget(self.baslik_label,0,0,1,4)
        self.layout.addWidget(self.urun_label,1,0)
        self.layout.addWidget(self.urun_combo,1,1)
        self.layout.addWidget(self.goster_button,1,2)
        self.layout.addWidget(self.fiyat_label,2,0)
        self.layout.addWidget(self.fiyat_lineedit,2,1,1,2)
        self.layout.addWidget(self.tahmin_label,3,0)
        self.layout.addWidget(self.tahmin_sonuc,3,1)
        self.layout.addWidget(self.fiyat_sonuc_label,3,2)

        self.setLayout(self.layout)

        self.setWindowTitle("Distribütörler İçin Fiyat Analiz Programı (DİFAP)")
        self.setWindowIcon(QIcon("Icon.png"))
        self.setStyleSheet("background-color: #383838; color: white;")

    def Sonuc_Goster(self):
        # Hepsiburada
        """
        URL için comboboxtan gelen text verisinin türkçeden latince karakterlere çevrilmesi.

        """
        Tr2Eng = str.maketrans("çğıöşü", "cgiosu") # Sözlük
        urun_ad = self.urun_combo.currentText() # Comboboxtan veriyi çektik
        urun_ad = urun_ad.lower()
        urun_ad = urun_ad.translate(Tr2Eng) # Veriyi latince harfe çevirdik.

        #
        url = 'https://www.hepsiburada.com/ara?q={}&siralama=coksatan'.format(urun_ad) # Ürün adını urlnin içine yerleştirdik.
        res = requests.get(url)
        soup = bs4.BeautifulSoup(res.text, 'lxml')

        resb = soup.find_all(attrs={'class': 'price product-price'}) # Fiyat verileri
        resc = []

        """
        Çektiğimiz sayfadaki fiyat verilerinden ilk 15 tanesini almak için.
        """
        for i in resb:
            if resb.index(i) == 15:
                break
            else:
                resc.append(i.text)


        ### Verinin temizlenmesi

        f = [x.replace(" ", "") for x in resc]
        g = [x.replace("TL", "") for x in f]
        h = [x.replace(".", "") for x in g]
        i = [x.replace(",", ".") for x in h]
        hepsiburada = [float(x) for x in i]

        self.hepsiburada1 = [] # Verilerin son hali
        for i in hepsiburada:
            self.hepsiburada1.append(("Hepsiburada", i)) #Her bir verinin yanına site adını yazdırdık.

        # N11
        url1 = "https://www.n11.com/outdoor-ve-kamp/kamp-malzemeleri?q={}&srt=SALES_VOLUME".format(urun_ad)
        res1 = requests.get(url1)
        soup1 = bs4.BeautifulSoup(res1.text, 'lxml')
        res1a = soup1.select('div > a > ins')
        res1b = []

        for i in res1a:
            res1b.append(i.text)

        res1b = res1b[5:] # En başta gelen istenmeyen verileri eledik.
        res1b = res1b[:15] # 15 tanesini aldık.
        res1c = [x.replace("\n", "") for x in res1b]
        res1d = [x.replace(" ", "") for x in res1c]
        res1e = [x.replace("TL", "") for x in res1d]
        res1f = [x.replace(".", "") for x in res1e]
        res1g = [x.replace(",", ".") for x in res1f]
        res1h = [float(x) for x in res1g]

        self.n11 = []
        for i in res1g:
            self.n11.append(("N11", i))


        # MySql Bağlantısı

        cnx = mdb.connect(user="root", database="urunler") # Veritabanına bağlantısı

        curA = cnx.cursor() # İşaretçi

        insert_data = "INSERT INTO fiyatlar(site_ad,urun_fiyat) VALUES(%s,%s)"

        try:
            curA.execute("CREATE TABLE fiyatlar(site_ad VARCHAR(55), urun_fiyat FLOAT(11)) ") # Fiyatlar tablosu oluşturma (yok ise)
            cnx.commit()
        except mdb.Error as err:
            print("Hata MYSQL2: {}".format(err))

        try:
            curA.execute("SELECT * FROM fiyatlar WHERE site_ad = 'Hepsiburada'")
            if curA.rowcount == 0:
                curA.executemany(insert_data, self.hepsiburada1)
                cnx.commit()
            else:
                pass

        except mdb.Error as err:
            print("Hata MYSQL1: {}".format(err))

        try:
            curA.execute("SELECT * FROM fiyatlar WHERE site_ad ='N11'")
            if curA.rowcount == 0:
                curA.executemany(insert_data, self.n11)
                cnx.commit()
            else:
                pass

        except mdb.Error as err:
            print("Hata MYSQL3: {}".format(err))


        # Numpy Ve Pandas

        curA.execute("SELECT * FROM fiyatlar")
        tablo = curA.fetchall() # İsaretçideki tüm verileri çektik
        dataframe = pd.DataFrame(tablo)
        dataframeHepsiburada = dataframe.head(15).loc[:, 1] # Tüm satırlar + index 1
        dataframeN11 = dataframe.tail(15).loc[:, 1]

        # Numpy Kısmı

        self.hepsiburadaort = np.average(dataframeHepsiburada) # Hepsiburada fiyat ortalaması
        self.hepsiburadaort = float("%.2f" % self.hepsiburadaort)
        self.n11ort = np.average(dataframeN11) # N11 Ortalaması
        self.n11ort = float("%.2f" % self.n11ort)



        self.tahmin_sonuc.setText("Hepsiburada\n-------------- \n{} \n\nN11\n-------------- \n{}".format(self.hepsiburadaort,self.n11ort)) # Iki sitenin de ortalamalarını yazdırdık.
        cnx.commit()
        cnx.close()

    def Temizle(self): # Combobox indexi değiştiğinde tablo temizlenir.
        cnx = mdb.connect(user="root", database="urunler")
        curA = cnx.cursor()

        curA.execute("DELETE FROM fiyatlar")
        cnx.commit()
        cnx.close()

    def Fiyat_Hesapla(self):
        try:
            fiyat_deg = float(self.fiyat_lineedit.text()) # Line Edite yazdığımız veriyi çektik.

            if fiyat_deg < self.hepsiburadaort and fiyat_deg < self.n11ort:

                self.fiyat_sonuc_label.setText("Ürünü her iki siteye de satabilirsiniz.")
            elif fiyat_deg < self.hepsiburadaort and fiyat_deg > self.n11ort:

                self.fiyat_sonuc_label.setText("Ürünü Hepsiburadaya satabilirsiniz.")
            elif fiyat_deg > self.hepsiburadaort and fiyat_deg < self.n11ort:

                self.fiyat_sonuc_label.setText("Ürünü N11'e satabilirsiniz.")
            else:
                self.fiyat_sonuc_label.setText("Ürünü kendiniz satmanız daha doğru olur.")
        except AttributeError:

            self.fiyat_sonuc_label.setText("Lütfen önce göster butonuna tıklayınız!")
        except ValueError:
            self.fiyat_sonuc_label.setText("Lütfen sayı giriniz!")


def except_hook(cls,exception,traceback): # PyQt5 Hatalarını yazdıran kod
    sys.__excepthook__(cls,exception,traceback)
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main = Arayuz()
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()