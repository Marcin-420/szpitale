# Service Area Analyzer - Analiza Dostępności do Szpitali w Warszawie 🏥

## 📋 Opis
Narzędzie ArcGIS Pro Python Toolbox do analizy dostępności przestrzennej do szpitali. Identyfikuje obszary o ograniczonym dostępie ("pustynie usługowe") i generuje szczegółowy raport HTML.

## 🎯 Funkcjonalności
- ✅ Tworzenie 3 stref dostępności (bliska/średnia/daleka)
- ✅ Analiza pokrycia obszarów mieszkalnych
- ✅ Identyfikacja pustyń usługowych
- ✅ Statystyki pokrycia ludności
- ✅ Raport HTML z wizualizacjami
- ✅ Pełna integracja z ArcGIS Pro

## 🔧 Wymagania
- **ArcGIS Pro 2.8+**
- **Python 3.7+** (wbudowany w ArcGIS Pro)
- **Spatial Analyst extension** (opcjonalnie)
- Dane wejściowe w układzie **PUWG 1992 (EPSG:2180)** - zalecane

## 📥 Instalacja

### Krok 1: Pobierz narzędzie
```bash
git clone https://github.com/Marcin-420/szpitale.git
cd szpitale
```

### Krok 2: Dodaj toolbox do ArcGIS Pro
1. Otwórz **ArcGIS Pro**
2. Otwórz **Catalog Pane** (View → Catalog Pane)
3. Rozwiń **Toolboxes**
4. Kliknij prawym → **Add Toolbox**
5. Wskaż plik `ServiceAreaAnalyzer.pyt`
6. Kliknij **OK**

Toolbox pojawi się jako **"Service Area Analyzer"** 🎉

## 🚀 Użycie

### 1. Przygotowanie danych
Upewnij się że dane są w układzie **PUWG 1992 (EPSG:2180)**:
```python
# Reprojektuj jeśli trzeba
arcpy.management.Project(
    in_dataset="szpitale_WGS84",
    out_dataset="szpitale_PUWG1992",
    out_coor_system="EPSG:2180"
)
```

### 2. Uruchomienie narzędzia
1. W Catalog Pane rozwiń **Service Area Analyzer**
2. Kliknij **"Analizator Dostępności do Szpitali"**
3. Wypełnij parametry:

| Parametr | Opis | Domyślnie |
|----------|------|-----------|
| Warstwa szpitali | Warstwa punktowa szpitali | - |
| Warstwa obszarów mieszkalnych | Warstwa poligonowa dzielnic/osiedli | - |
| Pole ludności | Pole z liczbą mieszkańców (opcjonalnie) | - |
| Strefa bliska | Odległość w metrach | 1000 m |
| Strefa średnia | Odległość w metrach | 3000 m |
| Strefa daleka | Odległość w metrach | 5000 m |
| Geodatabase wyjściowa | Lokalizacja wyników | - |
| Prefix warstw | Prefix nazw warstw wyjściowych | Hospital_Access |
| Generuj raport HTML | Czy utworzyć raport HTML | ✅ |
| Ścieżka raportu HTML | Ścieżka do pliku HTML | (automatyczna) |

4. Kliknij **Run** ⚡

### 3. Wyniki
Narzędzie wygeneruje:

**Warstwy wyjściowe:**
1. `Hospital_Access_Zone_close` - strefa bliska (bufor 1 km)
2. `Hospital_Access_Zone_medium` - strefa średnia (bufor 3 km)
3. `Hospital_Access_Zone_far` - strefa daleka (bufor 5 km)
4. `Hospital_Access_Residential_Analysis` - obszary z klasyfikacją dostępności
5. `Hospital_Access_Service_Deserts` - pustynie usługowe

**Raport HTML:**
- Parametry analizy
- Statystyki pokrycia
- Wnioski i rekomendacje
- Wizualizacje

## 📊 Interpretacja wyników

### Klasyfikacja dostępności:
- **Bliska** 🟢 - szpital w odległości < 1 km
- **Średnia** 🟡 - szpital w odległości 1-3 km
- **Daleka** 🟠 - szpital w odległości 3-5 km
- **Poza zasięgiem** 🔴 - szpital w odległości > 5 km
- **Brak dostępu** ⚫ - brak szpitali w promieniu 5 km

### Pustynie usługowe:
Obszary sklasyfikowane jako "Poza zasięgiem" lub "Brak dostępu" wymagają interwencji planistycznej.

## 🛠️ Rozwiązywanie problemów

### Problem: "No Parameters" w narzędziu
**Rozwiązanie:**
1. Zamknij narzędzie
2. Usuń toolbox z listy (prawym → Remove)
3. Dodaj ponownie (Add Toolbox)
4. Refresh (F5)

### Problem: Błąd "Invalid geometry"
**Rozwiązanie:**
Napraw geometrie:
```python
arcpy.management.RepairGeometry(warstwa, "DELETE_NULL")
```

### Problem: Różne układy współrzędnych
**Rozwiązanie:**
Reprojektuj do PUWG 1992:
```python
arcpy.management.Project(
    in_dataset=warstwa_wejsciowa,
    out_dataset=warstwa_wyjsciowa,
    out_coor_system="EPSG:2180"
)
```

### Problem: Błąd "Failed to execute"
**Rozwiązanie:**
1. Sprawdź czy geodatabase jest dostępna i nie jest używana przez inne narzędzie
2. Upewnij się, że warstwy wejściowe są poprawne (punkty dla szpitali, poligony dla obszarów)
3. Sprawdź czy masz prawa zapisu do geodatabase
4. Spróbuj uruchomić narzędzie z nowymi nazwami warstw wyjściowych

## 📚 Przykład użycia

```python
import arcpy

# Ustawienia
arcpy.env.workspace = r"C:\projekty\warszawa.gdb"
arcpy.env.overwriteOutput = True

# Uruchom narzędzie
arcpy.HospitalAccessibilityAnalyzer_ServiceAreaAnalyzer(
    hospitals_layer="szpitale_warszawa",
    residential_areas="dzielnice_warszawa",
    population_field="LUDNOSC",
    buffer_close=1000,
    buffer_medium=3000,
    buffer_far=5000,
    output_gdb=r"C:\projekty\warszawa.gdb",
    output_prefix="Hospital_Access",
    generate_html=True,
    report_path=r"C:\projekty\raport.html"
)
```

## 💡 Wskazówki

### Pobieranie danych szpitali z OpenStreetMap
Możesz pobrać dane szpitali używając Overpass Turbo:

1. Wejdź na [overpass-turbo.eu](https://overpass-turbo.eu/)
2. Użyj zapytania:
```
[out:json];
area["name"="Warszawa"]->.searchArea;
(
  node["amenity"="hospital"](area.searchArea);
  way["amenity"="hospital"](area.searchArea);
);
out center;
```
3. Kliknij **Run** (uruchom)
4. Eksportuj dane (Export → GeoJSON)
5. Zaimportuj do ArcGIS Pro

### Optymalizacja wydajności
- Używaj File Geodatabase zamiast shapefiles
- Upewnij się, że dane są w tym samym układzie współrzędnych
- Dla dużych zbiorów danych rozważ użycie spatial index
- Wyłącz zbędne rozszerzenia ArcGIS Pro podczas analizy

## 🔍 Metodologia

### Buffer Analysis
Narzędzie tworzy trzy koncentryczne bufory wokół szpitali:
- **Strefa 1 (bliska):** domyślnie 1000m - dostęp pieszy (12-15 min)
- **Strefa 2 (średnia):** domyślnie 3000m - dostęp rowerem/komunikacją (15-30 min)
- **Strefa 3 (daleka):** domyślnie 5000m - dostęp samochodem/komunikacją (30+ min)

### Near Analysis
Dla każdego obszaru mieszkalnego obliczana jest odległość do najbliższego szpitala używając funkcji `arcpy.analysis.Near`.

### Klasyfikacja
Obszary są klasyfikowane według odległości do najbliższego szpitala:
- Odległość euklidesowa (linia prosta)
- Klasyfikacja na 5 kategorii
- Identyfikacja pustyń usługowych

### Ograniczenia
⚠️ **Uwaga:** Analiza używa odległości euklidesowej (w linii prostej), która nie uwzględnia:
- Rzeczywistej sieci drogowej
- Barier naturalnych (rzeki, góry)
- Czasu dojazdu
- Dostępności komunikacji publicznej

Dla bardziej precyzyjnej analizy rozważ użycie **Network Analyst** z rzeczywistą siecią drogową.

## 🤝 Współpraca

Znalazłeś błąd lub masz pomysł na nową funkcjonalność?
1. Otwórz [Issue](https://github.com/Marcin-420/szpitale/issues)
2. Opisz problem lub propozycję
3. Poczekaj na odpowiedź

Chcesz wnieść wkład w kod?
1. Zrób fork repozytorium
2. Stwórz branch z opisową nazwą
3. Wprowadź zmiany
4. Stwórz Pull Request

## 📄 Licencja
MIT License - możesz swobodnie używać i modyfikować

Pełna treść licencji w pliku [LICENSE](LICENSE)

## 👨‍💻 Autor
- **Marcin-420**
- **GitHub:** https://github.com/Marcin-420
- **Projekt:** https://github.com/Marcin-420/szpitale

## 🔗 Przydatne linki
- [Dokumentacja ArcGIS Pro](https://pro.arcgis.com/en/pro-app/latest/arcpy/)
- [Python Toolbox Reference](https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/a-quick-tour-of-python-toolboxes.htm)
- [ArcPy Reference](https://pro.arcgis.com/en/pro-app/latest/arcpy/main/arcgis-pro-arcpy-reference.htm)
- [Overpass Turbo API](https://overpass-turbo.eu/) - pobieranie danych OSM
- [GUS - Dane statystyczne](https://stat.gov.pl/) - dane o ludności

## 📞 Kontakt
Problemy lub pytania? 
- Otwórz [Issue na GitHubie](https://github.com/Marcin-420/szpitale/issues)
- Sprawdź [istniejące Issues](https://github.com/Marcin-420/szpitale/issues?q=is%3Aissue)

## 🗺️ Roadmap

### Wersja 1.1 (planowana)
- [ ] Integracja z Network Analyst dla rzeczywistych czasów dojazdu
- [ ] Eksport wyników do PDF
- [ ] Wizualizacja map w raporcie HTML
- [ ] Wielojęzyczne wsparcie (EN, PL)

### Wersja 2.0 (planowana)
- [ ] Analiza dostępności czasowej (isochrones)
- [ ] Uwzględnienie rozkładów jazdy komunikacji publicznej
- [ ] Analiza wielokryterialna (odległość + czas + dostępność)
- [ ] Dashboard interaktywny (ArcGIS Dashboards)

## 🙏 Podziękowania
- **Esri** za ArcGIS Pro i dokumentację
- **OpenStreetMap** za otwarte dane geograficzne
- **Społeczność GIS** za wsparcie i inspirację

---

**⭐ Jeśli ten projekt był pomocny, zostaw gwiazdkę na GitHubie! ⭐**