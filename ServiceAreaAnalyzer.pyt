# -*- coding: utf-8 -*-
"""
Service Area Analyzer - Narzędzie do analizy dostępności przestrzennej
Autor: Marcin-420
Data: 2026-01-15
Wersja: 1.0
"""

import arcpy
import os
import datetime


class Toolbox(object):
    def __init__(self):
        """Definicja toolboxa."""
        self.label = "Service Area Analyzer"
        self.alias = "ServiceAreaAnalyzer"
        self.tools = [HospitalAccessibilityAnalyzer]


class HospitalAccessibilityAnalyzer(object):
    def __init__(self):
        """Inicjalizacja narzędzia."""
        self.label = "Analizator Dostępności do Szpitali"
        self.description = ("Analizuje dostępność przestrzenną do szpitali "
                           "poprzez tworzenie stref buforowych i identyfikację "
                           "obszarów o ograniczonym dostępie (pustyń usługowych).")
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Definicja parametrów narzędzia."""
        
        # Parametr 0: Warstwa szpitali
        param0 = arcpy.Parameter(
            displayName="Warstwa szpitali",
            name="hospitals_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.list = ["Point"]
        
        # Parametr 1: Warstwa obszarów mieszkalnych
        param1 = arcpy.Parameter(
            displayName="Warstwa obszarów mieszkalnych",
            name="residential_areas",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        param1.filter.list = ["Polygon"]
        
        # Parametr 2: Pole ludności
        param2 = arcpy.Parameter(
            displayName="Pole ludności (opcjonalne)",
            name="population_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input"
        )
        param2.parameterDependencies = [param1.name]
        param2.filter.list = ["Short", "Long", "Float", "Double"]
        
        # Parametr 3: Strefa bliska
        param3 = arcpy.Parameter(
            displayName="Strefa bliska (metry)",
            name="buffer_close",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )
        param3.value = 1000
        
        # Parametr 4: Strefa średnia
        param4 = arcpy.Parameter(
            displayName="Strefa średnia (metry)",
            name="buffer_medium",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )
        param4.value = 3000
        
        # Parametr 5: Strefa daleka
        param5 = arcpy.Parameter(
            displayName="Strefa daleka (metry)",
            name="buffer_far",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )
        param5.value = 5000
        
        # Parametr 6: Geodatabase wyjściowa
        param6 = arcpy.Parameter(
            displayName="Geodatabase wyjściowa",
            name="output_gdb",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        param6.filter.list = ["Local Database"]
        
        # Parametr 7: Prefix warstw wyjściowych
        param7 = arcpy.Parameter(
            displayName="Prefix warstw wyjściowych",
            name="output_prefix",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param7.value = "Hospital_Access"
        
        # Parametr 8: Generuj raport HTML
        param8 = arcpy.Parameter(
            displayName="Generuj raport HTML",
            name="generate_html",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        param8.value = True
        
        # Parametr 9: Ścieżka raportu HTML
        param9 = arcpy.Parameter(
            displayName="Ścieżka raportu HTML",
            name="report_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output"
        )
        param9.filter.list = ["html"]
        
        return [param0, param1, param2, param3, param4, param5, 
                param6, param7, param8, param9]

    def isLicensed(self):
        """Sprawdzenie licencji."""
        return True

    def updateParameters(self, parameters):
        """Aktualizacja parametrów na podstawie zmian użytkownika."""
        # Włącz/wyłącz ścieżkę raportu w zależności od checkbox
        if parameters[8].value:
            parameters[9].enabled = True
            if not parameters[9].altered:
                # Ustawienie domyślnej ścieżki
                if parameters[6].value:
                    gdb_path = str(parameters[6].value)
                    gdb_dir = os.path.dirname(gdb_path)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    parameters[9].value = os.path.join(
                        gdb_dir, 
                        f"Hospital_Access_Report_{timestamp}.html"
                    )
        else:
            parameters[9].enabled = False
        
        return

    def updateMessages(self, parameters):
        """Walidacja parametrów."""
        # Walidacja stref buforowych
        if parameters[3].value and parameters[4].value:
            if parameters[3].value >= parameters[4].value:
                parameters[3].setErrorMessage(
                    "Strefa bliska musi być mniejsza niż strefa średnia"
                )
        
        if parameters[4].value and parameters[5].value:
            if parameters[4].value >= parameters[5].value:
                parameters[4].setErrorMessage(
                    "Strefa średnia musi być mniejsza niż strefa daleka"
                )
        
        # Walidacja geodatabase
        if parameters[6].value:
            gdb_path = str(parameters[6].value)
            if not gdb_path.endswith('.gdb'):
                parameters[6].setErrorMessage(
                    "Ścieżka musi wskazywać na File Geodatabase (.gdb)"
                )
        
        return

    def execute(self, parameters, messages):
        """Główna logika wykonania analizy."""
        try:
            # Pobranie parametrów
            hospitals = parameters[0].valueAsText
            residential = parameters[1].valueAsText
            pop_field = parameters[2].valueAsText
            buffer_close = float(parameters[3].value)
            buffer_medium = float(parameters[4].value)
            buffer_far = float(parameters[5].value)
            output_gdb = parameters[6].valueAsText
            prefix = parameters[7].valueAsText
            generate_html = parameters[8].value
            report_path = parameters[9].valueAsText if parameters[9].value else None
            
            arcpy.AddMessage("=" * 50)
            arcpy.AddMessage("Rozpoczęcie analizy dostępności do szpitali")
            arcpy.AddMessage("=" * 50)
            
            # Krok 1: Walidacja danych wejściowych
            arcpy.AddMessage("\n[1/6] Walidacja danych wejściowych...")
            
            # Sprawdzenie liczby szpitali
            hospital_count = int(arcpy.management.GetCount(hospitals)[0])
            arcpy.AddMessage(f"  → Znaleziono {hospital_count} szpitali")
            
            if hospital_count == 0:
                arcpy.AddError("Brak szpitali w warstwie wejściowej!")
                return
            
            # Sprawdzenie obszarów mieszkalnych
            residential_count = int(arcpy.management.GetCount(residential)[0])
            arcpy.AddMessage(f"  → Znaleziono {residential_count} obszarów mieszkalnych")
            
            if residential_count == 0:
                arcpy.AddError("Brak obszarów mieszkalnych w warstwie wejściowej!")
                return
            
            # Krok 2: Tworzenie buforów
            arcpy.AddMessage("\n[2/6] Tworzenie stref dostępności...")
            
            buffer_close_fc = os.path.join(output_gdb, f"{prefix}_Zone_close")
            buffer_medium_fc = os.path.join(output_gdb, f"{prefix}_Zone_medium")
            buffer_far_fc = os.path.join(output_gdb, f"{prefix}_Zone_far")
            
            arcpy.AddMessage(f"  → Tworzenie strefy bliskiej ({buffer_close}m)...")
            arcpy.analysis.Buffer(
                in_features=hospitals,
                out_feature_class=buffer_close_fc,
                buffer_distance_or_field=f"{buffer_close} Meters",
                dissolve_option="ALL"
            )
            
            arcpy.AddMessage(f"  → Tworzenie strefy średniej ({buffer_medium}m)...")
            arcpy.analysis.Buffer(
                in_features=hospitals,
                out_feature_class=buffer_medium_fc,
                buffer_distance_or_field=f"{buffer_medium} Meters",
                dissolve_option="ALL"
            )
            
            arcpy.AddMessage(f"  → Tworzenie strefy dalekiej ({buffer_far}m)...")
            arcpy.analysis.Buffer(
                in_features=hospitals,
                out_feature_class=buffer_far_fc,
                buffer_distance_or_field=f"{buffer_far} Meters",
                dissolve_option="ALL"
            )
            
            # Krok 3: Analiza pokrycia obszarów mieszkalnych
            arcpy.AddMessage("\n[3/6] Analiza pokrycia obszarów mieszkalnych...")
            
            # Kopiowanie warstwy mieszkalnej dla analizy
            analysis_fc = os.path.join(output_gdb, f"{prefix}_Residential_Analysis")
            arcpy.management.CopyFeatures(residential, analysis_fc)
            
            # Dodanie pola klasyfikacji
            arcpy.AddMessage("  → Dodawanie pola klasyfikacji...")
            field_name = "ACCESS_CLASS"
            arcpy.management.AddField(
                in_table=analysis_fc,
                field_name=field_name,
                field_type="TEXT",
                field_length=50
            )
            
            # Obliczenie odległości do najbliższego szpitala
            arcpy.AddMessage("  → Obliczanie odległości do najbliższych szpitali...")
            arcpy.analysis.Near(
                in_features=analysis_fc,
                near_features=hospitals,
                search_radius=f"{buffer_far} Meters"
            )
            
            # Klasyfikacja według odległości
            arcpy.AddMessage("  → Klasyfikacja obszarów według dostępności...")
            with arcpy.da.UpdateCursor(analysis_fc, ["NEAR_DIST", field_name]) as cursor:
                for row in cursor:
                    distance = row[0]
                    if distance == -1 or distance is None:
                        row[1] = "Brak dostępu"
                    elif distance <= buffer_close:
                        row[1] = "Bliska"
                    elif distance <= buffer_medium:
                        row[1] = "Średnia"
                    elif distance <= buffer_far:
                        row[1] = "Daleka"
                    else:
                        row[1] = "Poza zasięgiem"
                    cursor.updateRow(row)
            
            # Krok 4: Obliczanie statystyk
            arcpy.AddMessage("\n[4/6] Obliczanie statystyk pokrycia...")
            
            zone_counts = {
                "Bliska": 0,
                "Średnia": 0,
                "Daleka": 0,
                "Poza zasięgiem": 0,
                "Brak dostępu": 0
            }
            
            zone_population = {
                "Bliska": 0,
                "Średnia": 0,
                "Daleka": 0,
                "Poza zasięgiem": 0,
                "Brak dostępu": 0
            }
            
            total_population = 0
            
            # Zliczanie obszarów i populacji
            if pop_field:
                fields = [field_name, pop_field]
            else:
                fields = [field_name]
            
            with arcpy.da.SearchCursor(analysis_fc, fields) as cursor:
                for row in cursor:
                    access_class = row[0]
                    if access_class in zone_counts:
                        zone_counts[access_class] += 1
                        if pop_field and len(row) > 1 and row[1] is not None:
                            population = float(row[1])
                            zone_population[access_class] += population
                            total_population += population
            
            # Wyświetlenie statystyk
            arcpy.AddMessage("  Statystyki pokrycia obszarów:")
            for zone, count in zone_counts.items():
                if total_population > 0:
                    pop = zone_population[zone]
                    pct = (pop / total_population * 100) if total_population > 0 else 0
                    arcpy.AddMessage(f"    {zone}: {count} obszarów, {int(pop)} mieszkańców ({pct:.1f}%)")
                else:
                    arcpy.AddMessage(f"    {zone}: {count} obszarów")
            
            # Krok 5: Identyfikacja pustyń usługowych
            arcpy.AddMessage("\n[5/6] Identyfikacja pustyń usługowych...")
            
            deserts_fc = os.path.join(output_gdb, f"{prefix}_Service_Deserts")
            
            where_clause = f"{field_name} IN ('Poza zasięgiem', 'Brak dostępu')"
            desert_layer = arcpy.management.MakeFeatureLayer(
                analysis_fc, 
                "desert_temp",
                where_clause
            )
            
            desert_count = int(arcpy.management.GetCount(desert_layer)[0])
            
            if desert_count > 0:
                arcpy.management.CopyFeatures(desert_layer, deserts_fc)
                arcpy.AddMessage(f"  → Zidentyfikowano {desert_count} pustyń usługowych")
            else:
                # Utwórz pustą warstwę
                arcpy.management.CreateFeatureclass(
                    out_path=output_gdb,
                    out_name=f"{prefix}_Service_Deserts",
                    geometry_type="POLYGON",
                    spatial_reference=arcpy.Describe(analysis_fc).spatialReference
                )
                arcpy.AddMessage("  → Nie znaleziono pustyń usługowych (doskonały wynik!)")
            
            # Krok 6: Generowanie raportu HTML
            if generate_html and report_path:
                arcpy.AddMessage("\n[6/6] Generowanie raportu HTML...")
                
                report_data = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "hospitals_count": hospital_count,
                    "residential_count": residential_count,
                    "buffer_close": buffer_close,
                    "buffer_medium": buffer_medium,
                    "buffer_far": buffer_far,
                    "has_population": pop_field is not None
                }
                
                html_content = self.generate_html_report(
                    report_data,
                    zone_counts,
                    zone_population,
                    total_population,
                    desert_count
                )
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                arcpy.AddMessage(f"  → Raport zapisany: {report_path}")
            else:
                arcpy.AddMessage("\n[6/6] Pomijam generowanie raportu HTML")
            
            # Podsumowanie
            arcpy.AddMessage("\n" + "=" * 50)
            arcpy.AddMessage("✓ Analiza zakończona pomyślnie!")
            arcpy.AddMessage("=" * 50)
            arcpy.AddMessage("\nWygenerowane warstwy:")
            arcpy.AddMessage(f"  1. {prefix}_Zone_close")
            arcpy.AddMessage(f"  2. {prefix}_Zone_medium")
            arcpy.AddMessage(f"  3. {prefix}_Zone_far")
            arcpy.AddMessage(f"  4. {prefix}_Residential_Analysis")
            arcpy.AddMessage(f"  5. {prefix}_Service_Deserts")
            
        except arcpy.ExecuteError:
            arcpy.AddError(f"Błąd ArcGIS: {arcpy.GetMessages(2)}")
        except Exception as e:
            arcpy.AddError(f"Błąd wykonania: {str(e)}")
            import traceback
            arcpy.AddError(traceback.format_exc())

    def generate_html_report(self, report_data, zone_counts, zone_population, 
                            total_population, desert_count):
        """Generuje raport HTML z analizy dostępności.
        
        WAŻNE: Wszystkie selektory CSS MUSZĄ zaczynać się od kropki!
        """
        
        # Przygotowanie danych statystycznych
        timestamp = report_data["timestamp"]
        hospitals_count = report_data["hospitals_count"]
        residential_count = report_data["residential_count"]
        buffer_close = report_data["buffer_close"]
        buffer_medium = report_data["buffer_medium"]
        buffer_far = report_data["buffer_far"]
        has_population = report_data["has_population"]
        
        # Obliczenia procentowe
        if total_population > 0:
            pct_close = (zone_population["Bliska"] / total_population * 100)
            pct_medium = (zone_population["Średnia"] / total_population * 100)
            pct_far = (zone_population["Daleka"] / total_population * 100)
            pct_outside = (zone_population["Poza zasięgiem"] / total_population * 100)
            pct_none = (zone_population["Brak dostępu"] / total_population * 100)
            pct_good = pct_close + pct_medium + pct_far
        else:
            pct_close = pct_medium = pct_far = pct_outside = pct_none = pct_good = 0
        
        # Generowanie HTML
        html = f'''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport: Analiza Dostępności do Szpitali</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 20px;
        }}
        .info-box {{
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .success-box {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border: 2px solid #e9ecef;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #6c757d;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .zone-close {{ color: #28a745; font-weight: bold; }}
        .zone-medium {{ color: #ffc107; font-weight: bold; }}
        .zone-far {{ color: #fd7e14; font-weight: bold; }}
        .zone-out {{ color: #dc3545; font-weight: bold; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .parameter-table {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        .parameter-table p {{
            margin: 8px 0;
        }}
        .parameter-table strong {{
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Raport: Analiza Dostępności do Szpitali w Warszawie</h1>
        
        <div class="info-box">
            <p><strong>📅 Data wygenerowania:</strong> {timestamp}</p>
            <p><strong>🔧 Narzędzie:</strong> Service Area Analyzer v1.0</p>
            <p><strong>👤 Autor:</strong> Marcin-420</p>
        </div>

        <h2>📊 Parametry Analizy</h2>
        <div class="parameter-table">
            <p><strong>Liczba szpitali:</strong> {hospitals_count}</p>
            <p><strong>Liczba obszarów mieszkalnych:</strong> {residential_count}</p>
            <p><strong>Strefa bliska:</strong> {int(buffer_close)} metrów (≤ {int(buffer_close)}m)</p>
            <p><strong>Strefa średnia:</strong> {int(buffer_medium)} metrów ({int(buffer_close)}-{int(buffer_medium)}m)</p>
            <p><strong>Strefa daleka:</strong> {int(buffer_far)} metrów ({int(buffer_medium)}-{int(buffer_far)}m)</p>
            {'<p><strong>Dane populacji:</strong> ✓ Dostępne</p>' if has_population else '<p><strong>Dane populacji:</strong> ✗ Brak danych</p>'}
        </div>

        <h2>📈 Statystyki Pokrycia</h2>
        
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value zone-close">{zone_counts['Bliska']}</div>
                <div class="stat-label">Obszarów w strefie bliskiej</div>
                {f'<div style="color: #28a745; font-weight: bold; margin-top: 10px;">{int(zone_population["Bliska"]):,} mieszkańców ({pct_close:.1f}%)</div>' if has_population and total_population > 0 else ''}
            </div>
            
            <div class="stat-card">
                <div class="stat-value zone-medium">{zone_counts['Średnia']}</div>
                <div class="stat-label">Obszarów w strefie średniej</div>
                {f'<div style="color: #ffc107; font-weight: bold; margin-top: 10px;">{int(zone_population["Średnia"]):,} mieszkańców ({pct_medium:.1f}%)</div>' if has_population and total_population > 0 else ''}
            </div>
            
            <div class="stat-card">
                <div class="stat-value zone-far">{zone_counts['Daleka']}</div>
                <div class="stat-label">Obszarów w strefie dalekiej</div>
                {f'<div style="color: #fd7e14; font-weight: bold; margin-top: 10px;">{int(zone_population["Daleka"]):,} mieszkańców ({pct_far:.1f}%)</div>' if has_population and total_population > 0 else ''}
            </div>
            
            <div class="stat-card">
                <div class="stat-value zone-out">{zone_counts['Poza zasięgiem'] + zone_counts['Brak dostępu']}</div>
                <div class="stat-label">Pustyń usługowych</div>
                {f'<div style="color: #dc3545; font-weight: bold; margin-top: 10px;">{int(zone_population["Poza zasięgiem"] + zone_population["Brak dostępu"]):,} mieszkańców ({pct_outside + pct_none:.1f}%)</div>' if has_population and total_population > 0 else ''}
            </div>
        </div>

        <h2>📋 Szczegółowe Zestawienie</h2>
        <table>
            <thead>
                <tr>
                    <th>Kategoria Dostępności</th>
                    <th>Liczba Obszarów</th>
                    {'<th>Populacja</th>' if has_population else ''}
                    {'<th>Procent Populacji</th>' if has_population and total_population > 0 else ''}
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="zone-close">🟢 Bliska</span> (≤ {int(buffer_close)}m)</td>
                    <td>{zone_counts['Bliska']}</td>
                    {f'<td>{int(zone_population["Bliska"]):,}</td>' if has_population else ''}
                    {f'<td>{pct_close:.1f}%</td>' if has_population and total_population > 0 else ''}
                </tr>
                <tr>
                    <td><span class="zone-medium">🟡 Średnia</span> ({int(buffer_close)}-{int(buffer_medium)}m)</td>
                    <td>{zone_counts['Średnia']}</td>
                    {f'<td>{int(zone_population["Średnia"]):,}</td>' if has_population else ''}
                    {f'<td>{pct_medium:.1f}%</td>' if has_population and total_population > 0 else ''}
                </tr>
                <tr>
                    <td><span class="zone-far">🟠 Daleka</span> ({int(buffer_medium)}-{int(buffer_far)}m)</td>
                    <td>{zone_counts['Daleka']}</td>
                    {f'<td>{int(zone_population["Daleka"]):,}</td>' if has_population else ''}
                    {f'<td>{pct_far:.1f}%</td>' if has_population and total_population > 0 else ''}
                </tr>
                <tr>
                    <td><span class="zone-out">🔴 Poza zasięgiem</span> (> {int(buffer_far)}m)</td>
                    <td>{zone_counts['Poza zasięgiem']}</td>
                    {f'<td>{int(zone_population["Poza zasięgiem"]):,}</td>' if has_population else ''}
                    {f'<td>{pct_outside:.1f}%</td>' if has_population and total_population > 0 else ''}
                </tr>
                <tr>
                    <td><span class="zone-out">⚫ Brak dostępu</span></td>
                    <td>{zone_counts['Brak dostępu']}</td>
                    {f'<td>{int(zone_population["Brak dostępu"]):,}</td>' if has_population else ''}
                    {f'<td>{pct_none:.1f}%</td>' if has_population and total_population > 0 else ''}
                </tr>
            </tbody>
        </table>

        <h2>🎯 Wnioski i Rekomendacje</h2>
        '''
        
        # Dynamiczne wnioski na podstawie wyników
        if desert_count == 0:
            html += '''
        <div class="success-box">
            <h3>✅ Doskonały poziom dostępności!</h3>
            <p>Wszystkie obszary mieszkalne mają dostęp do szpitali w akceptowalnej odległości. Nie zidentyfikowano pustyń usługowych.</p>
        </div>
        '''
        elif pct_good > 90 and has_population and total_population > 0:
            html += f'''
        <div class="success-box">
            <h3>✅ Bardzo dobry poziom dostępności</h3>
            <p><strong>{pct_good:.1f}%</strong> populacji ma dostęp do szpitali w odległości do {int(buffer_far)}m. Jest to bardzo dobry wynik.</p>
            <p>Zidentyfikowano {desert_count} pustyń usługowych wymagających uwagi.</p>
        </div>
        '''
        elif pct_good > 70 and has_population and total_population > 0:
            html += f'''
        <div class="warning-box">
            <h3>⚠️ Dobry poziom dostępności z obszarami do poprawy</h3>
            <p><strong>{pct_good:.1f}%</strong> populacji ma dostęp do szpitali. Jednakże <strong>{pct_outside + pct_none:.1f}%</strong> populacji ({int(zone_population["Poza zasięgiem"] + zone_population["Brak dostępu"]):,} osób) mieszka w obszarach o ograniczonym dostępie.</p>
            <p><strong>Zidentyfikowano {desert_count} pustyń usługowych</strong> wymagających interwencji planistycznej.</p>
        </div>
        '''
        else:
            html += f'''
        <div class="warning-box">
            <h3>⚠️ Obszary wymagające poprawy</h3>
            <p>Zidentyfikowano <strong>{desert_count} pustyń usługowych</strong> - obszarów o znacznie ograniczonym dostępie do szpitali.</p>
            {'<p><strong>' + f'{pct_outside + pct_none:.1f}%' + '</strong> populacji (' + f'{int(zone_population["Poza zasięgiem"] + zone_population["Brak dostępu"]):,}' + ' osób) mieszka w obszarach o ograniczonym dostępie.</p>' if has_population and total_population > 0 else ''}
        </div>
        '''
        
        html += '''
        <h3>📌 Rekomendacje:</h3>
        <ul>
        '''
        
        if desert_count > 0:
            html += f'''
            <li><strong>Priorytet 1:</strong> Szczegółowa analiza {desert_count} zidentyfikowanych pustyń usługowych</li>
            <li><strong>Priorytet 2:</strong> Rozważenie lokalizacji nowych placówek w obszarach deficytowych</li>
            <li><strong>Priorytet 3:</strong> Poprawa infrastruktury komunikacyjnej w obszarach o ograniczonym dostępie</li>
            '''
        
        html += '''
            <li>Regularna aktualizacja analizy (co najmniej raz na rok)</li>
            <li>Uwzględnienie czasu dojazdu, nie tylko odległości euclidesowej</li>
            <li>Analiza rozkładu czasowego obciążenia szpitali</li>
            <li>Integracja z danymi demograficznymi (starzenie się społeczeństwa)</li>
        </ul>

        <h2>🗺️ Warstwy Wyjściowe</h2>
        <div class="info-box">
            <p>Analiza wygenerowała następujące warstwy w geodatabase:</p>
            <ol>
                <li><strong>*_Zone_close</strong> - strefa bliska ({int(buffer_close)}m)</li>
                <li><strong>*_Zone_medium</strong> - strefa średnia ({int(buffer_medium)}m)</li>
                <li><strong>*_Zone_far</strong> - strefa daleka ({int(buffer_far)}m)</li>
                <li><strong>*_Residential_Analysis</strong> - obszary mieszkalne z klasyfikacją dostępności</li>
                <li><strong>*_Service_Deserts</strong> - zidentyfikowane pustynie usługowe</li>
            </ol>
        </div>

        <h2>ℹ️ Metodologia</h2>
        <div class="info-box">
            <p><strong>Metoda analizy:</strong> Buffer Analysis + Near Analysis</p>
            <p><strong>Typ odległości:</strong> Odległość euklidesowa (linia prosta)</p>
            <p><strong>Klasyfikacja:</strong></p>
            <ul>
                <li><strong>Bliska:</strong> odległość ≤ {int(buffer_close)}m</li>
                <li><strong>Średnia:</strong> odległość {int(buffer_close)}-{int(buffer_medium)}m</li>
                <li><strong>Daleka:</strong> odległość {int(buffer_medium)}-{int(buffer_far)}m</li>
                <li><strong>Poza zasięgiem:</strong> odległość > {int(buffer_far)}m</li>
                <li><strong>Brak dostępu:</strong> brak szpitala w promieniu analizy</li>
            </ul>
            <p><strong>Uwaga:</strong> Analiza opiera się na odległości w linii prostej. Rzeczywiste czasy dojazdu mogą być dłuższe ze względu na infrastrukturę komunikacyjną.</p>
        </div>

        <div class="footer">
            <p><strong>Service Area Analyzer v1.0</strong></p>
            <p>Narzędzie ArcGIS Pro Python Toolbox</p>
            <p>© 2026 Marcin-420 | <a href="https://github.com/Marcin-420/szpitale" target="_blank">GitHub</a></p>
            <p>Wygenerowano: {timestamp}</p>
        </div>
    </div>
</body>
</html>'''
        
        return html
