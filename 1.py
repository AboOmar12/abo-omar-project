"""
EV Route Planner - Ultimate Version
النسخة النهائية - تلقائي 100%
V21 - The Original V11 Code, Repaired
(V11 UI + V16 Colab Bridge Fix)
"""

import requests
import folium
from folium import plugins
from IPython.display import display, HTML, clear_output
import ipywidgets as widgets
from geopy.geocoders import Nominatim
import time
import threading
from google.colab import output # الواجهة الصحيحة
import json # لإرسال النتائج بشكل آمن

# --- الوظائف المساعدة (من V11) ---

def get_address_from_coords(lat, lon):
    """Get address from coordinates"""
    try:
        geolocator = Nominatim(user_agent="ev_route_planner_v21")
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if location:
            return location.address
        return f"{lat:.4f}, {lon:.4f}"
    except:
        return f"{lat:.4f}, {lon:.4f}"


def get_route_osrm(start_coords, end_coords):
    """Get route from OSRM"""
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
        params = {'overview': 'full', 'geometries': 'geojson'}
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        if data['code'] == 'Ok' and data['routes']:
            return data['routes'][0]
        return None
    except:
        return None


def divide_route_into_sections(route_coords, num_sections=3):
    """Divide route into sections"""
    total_points = len(route_coords)
    points_per_section = total_points // num_sections
    sections = []
    for i in range(num_sections):
        start_idx = i * points_per_section
        if i == num_sections - 1:
            end_idx = total_points
        else:
            end_idx = (i + 1) * points_per_section + 1
        sections.append(route_coords[start_idx:end_idx])
    return sections

# --- الكلاس الرئيسي (من V11) ---

class FullyAutomaticEVPlanner:
    """Fully automatic EV route planner - V11 architecture"""
    
    def __init__(self):
        self.start_coords = None
        self.end_coords = None
        self.start_address = None
        self.end_address = None
        self.route_data = None
        self.map_widget = None
        
        # EV Parameters with auto-update
        self.start_soc = widgets.FloatSlider(
            value=90, min=10, max=100, step=5,
            description='🔋 شحن البطارية:',
            style={'description_width': '150px'},
            layout=widgets.Layout(width='500px'),
            readout_format='.0f'
        )
        
        self.battery_capacity = widgets.FloatSlider(
            value=75, min=20, max=150, step=5,
            description='⚡ سعة البطارية (kWh):',
            style={'description_width': '150px'},
            layout=widgets.Layout(width='500px'),
            readout_format='.0f'
        )
        
        self.ev_efficiency = widgets.FloatSlider(
            value=5.0, min=2.0, max=10.0, step=0.5,
            description='📊 الكفاءة (km/kWh):',
            style={'description_width': '150px'},
            layout=widgets.Layout(width='500px'),
            readout_format='.1f'
        )
        
        self.fuel_consumption = widgets.FloatSlider(
            value=8.0, min=4.0, max=20.0, step=0.5,
            description='⛽ استهلاك وقود (L/100km):',
            style={'description_width': '150px'},
            layout=widgets.Layout(width='500px'),
            readout_format='.1f'
        )
        
        # Observe changes for auto-update
        self.start_soc.observe(self.on_param_change, 'value')
        self.battery_capacity.observe(self.on_param_change, 'value')
        self.ev_efficiency.observe(self.on_param_change, 'value')
        self.fuel_consumption.observe(self.on_param_change, 'value')
        
        # Output widgets
        self.results_output = widgets.Output()
        self.map_output = widgets.Output()
        self.status_output = widgets.Output()
        
    def on_param_change(self, change):
        """Auto-update when parameters change"""
        if self.route_data:
            with self.status_output:
                clear_output(wait=True)
                display(HTML("""
                    <div style="background: #2196F3; color: white; padding: 10px; border-radius: 8px; 
                                text-align: center; font-size: 14px; margin: 10px 0;">
                        🔄 جاري تحديث النتائج... / Updating results...
                    </div>
                """))
            time.sleep(0.3)
            self.calculate_and_display()
    
    def process_route(self, start_lat, start_lon, end_lat, end_lon):
        """Process route automatically (This is the function JS will call)"""
        
        with self.status_output:
            clear_output(wait=True)
            display(HTML("""
                <div style="background: #4CAF50; color: white; padding: 15px; border-radius: 10px; 
                            text-align: center; font-size: 15px; margin: 15px 0; 
                            box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                    ⏳ جاري معالجة المسار تلقائياً (V21)... / Processing route automatically (V21)...
                </div>
            """))
        
        self.start_coords = [start_lon, start_lat] # OSRM format
        self.end_coords = [end_lon, end_lat]     # OSRM format
        
        # Get addresses
        with self.status_output:
            clear_output(wait=True)
            display(HTML("""
                <div style="background: #2196F3; color: white; padding: 15px; border-radius: 10px; 
                            text-align: center; font-size: 15px; margin: 15px 0;">
                    📍 جاري جلب العناوين... / Fetching addresses...
                </div>
            """))
        
        self.start_address = get_address_from_coords(start_lat, start_lon)
        time.sleep(1) # Respect Nominatim rate limit
        self.end_address = get_address_from_coords(end_lat, end_lon)
        
        # Get route
        with self.status_output:
            clear_output(wait=True)
            display(HTML("""
                <div style="background: #FF9800; color: white; padding: 15px; border-radius: 10px; 
                            text-align: center; font-size: 15px; margin: 15px 0;">
                    🗺️ جاري حساب المسار... / Calculating route...
                </div>
            """))
        
        route = get_route_osrm(self.start_coords, self.end_coords)
        
        if route:
            self.route_data = {
                'coordinates': route['geometry']['coordinates'],
                'distance': route['distance'],
                'duration': route['duration']
            }
            
            with self.status_output:
                clear_output(wait=True)
                display(HTML("""
                    <div style="background: #4CAF50; color: white; padding: 15px; border-radius: 10px; 
                                text-align: center; font-size: 16px; margin: 15px 0; 
                                box-shadow: 0 4px 12px rgba(76,175,80,0.3);">
                        ✅ تم! جاري عرض النتائج... / Done! Displaying results...
                    </div>
                """))
            
            time.sleep(0.5)
            self.calculate_and_display()
        else:
            with self.status_output:
                clear_output(wait=True)
                display(HTML("""
                    <div style="background: #f44336; color: white; padding: 15px; border-radius: 10px; 
                                text-align: center; font-size: 15px; margin: 15px 0;">
                        ❌ فشل في حساب المسار / Failed to calculate route
                    </div>
                """))
        
        # إرجاع نتيجة لـ JS (مهم لـ .then() في JS)
        return json.dumps({'status': 'success', 'start': self.start_address, 'end': self.end_address})
    
    def calculate_and_display(self):
        """Calculate and display all results (V11 Logic)"""
        
        if not self.route_data:
            return
        
        # Clear status
        with self.status_output:
            clear_output(wait=True)
        
        # (نفس منطق الحسابات والـ HTML من V11)
        distance_km = self.route_data['distance'] / 1000
        duration_min = self.route_data['duration'] / 60
        duration_hours = duration_min / 60
        leg_distance = distance_km / 3
        
        total_range = self.battery_capacity.value * self.ev_efficiency.value
        current_range = total_range * (self.start_soc.value / 100)
        
        cp1_status = "operational"
        cp2_status = "operational"
        cp1_color = "lightblue"
        cp2_color = "lightblue"
        
        if ("Kharj" in self.start_address or "خرج" in self.start_address) and \
           ("Makkah" in self.end_address or "مكة" in self.end_address):
            cp1_status = "maintenance"
            cp1_color = "red"
        
        trip_possible = True
        failure_reason = ""
        
        if cp1_status == "maintenance":
            trip_possible = False
            failure_reason = f"محطة الشحن الأولى ({round(leg_distance,1)} كم) تحت الصيانة"
        elif current_range < leg_distance:
            trip_possible = False
            shortfall = leg_distance - current_range
            failure_reason = f"لن تصل للمحطة الأولى. ينقصك {round(shortfall, 1)} كم"
        
        if trip_possible:
            current_range = total_range
            if cp2_status == "maintenance":
                trip_possible = False
                failure_reason = "محطة الشحن الثانية تحت الصيانة"
            elif current_range < leg_distance:
                trip_possible = False
                failure_reason = "لن تصل للمحطة الثانية"
        
        if trip_possible:
            current_range = total_range
            if current_range < leg_distance:
                trip_possible = False
                failure_reason = "لن تصل للوجهة النهائية"
        
        fuel_cost = (distance_km / 100) * self.fuel_consumption.value * 2.33
        ev_cost = (distance_km / self.ev_efficiency.value) * 0.18
        savings = fuel_cost - ev_cost
        savings_pct = (savings / fuel_cost * 100) if fuel_cost > 0 else 0
        
        if trip_possible:
            status_color = "#27ae60"
            status_icon = "✅"
            status_msg = "نعم، يمكنك إتمام هذه الرحلة!"
            status_detail = f"ستتوقف عند محطتي شحن. المسافة لكل مرحلة: {round(leg_distance,1)} كم"
        else:
            status_color = "#e74c3c"
            status_icon = "❌"
            status_msg = "لا، هذه الرحلة مستحيلة"
            status_detail = failure_reason
        
        duration_display = f"{round(duration_hours, 1)} ساعة" if duration_hours >= 1 else f"{round(duration_min)} دقيقة"
        
        # Display results
        with self.results_output:
            clear_output(wait=True)
            
            # (لصق كود V11 HTML بالكامل)
            results_html = f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 30px; border-radius: 20px; color: white; margin: 25px 0;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3); animation: fadeIn 0.5s;">
                
                <h1 style="text-align: center; margin: 0 0 25px 0; font-size: 2.2em;">
                    📊 نتائج التحليل التلقائي
                </h1>
                
                <div style="background: rgba(255,255,255,0.15); padding: 18px; border-radius: 12px; margin-bottom: 20px;">
                    <div style="font-size: 1.1em; margin-bottom: 10px; display: flex; align-items: start;">
                        <strong style="min-width: 60px;">📍 من:</strong>
                        <span style="flex: 1;">{self.start_address}</span>
                    </div>
                    <div style="font-size: 1.1em; display: flex; align-items: start;">
                        <strong style="min-width: 60px;">📍 إلى:</strong>
                        <span style="flex: 1;">{self.end_address}</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 20px;">
                    <div style="background: rgba(255,255,255,0.25); padding: 25px; border-radius: 15px; text-align: center;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <div style="font-size: 3em; font-weight: bold; margin-bottom: 8px;">{round(distance_km, 1)}</div>
                        <div style="font-size: 1.2em;">🛣️ كيلومتر</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.25); padding: 25px; border-radius: 15px; text-align: center;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <div style="font-size: 3em; font-weight: bold; margin-bottom: 8px;">{duration_display}</div>
                        <div style="font-size: 1.2em;">⏱️ المدة</div>
                    </div>
                </div>
                
                <div style="background: {status_color}; padding: 25px; border-radius: 18px; margin: 20px 0;
                            box-shadow: 0 6px 20px rgba(0,0,0,0.2);">
                    <h2 style="text-align: center; margin: 0 0 18px 0; font-size: 1.7em;">
                        🧠 نتيجة التحليل
                    </h2>
                    <div style="background: rgba(0,0,0,0.2); padding: 25px; border-radius: 12px; text-align: center;">
                        <div style="font-size: 1.8em; font-weight: bold; margin-bottom: 12px;">
                            {status_icon} {status_msg}
                        </div>
                        <div style="font-size: 1.2em; line-height: 1.6;">
                            {status_detail}
                        </div>
                    </div>
                </div>
            """
            
            if trip_possible:
                results_html += f"""
                <div style="background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
                            padding: 25px; border-radius: 18px; margin: 20px 0;
                            box-shadow: 0 6px 20px rgba(0,0,0,0.2);">
                    <h2 style="text-align: center; margin: 0 0 20px 0; font-size: 1.7em;">
                        💰 مقارنة التكلفة
                    </h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                        <div style="background: rgba(255,255,255,0.25); padding: 25px; border-radius: 15px; text-align: center;">
                            <div style="font-size: 4em; margin-bottom: 12px;">⛽</div>
                            <div style="font-size: 2.2em; font-weight: bold; margin-bottom: 8px;">
                                {round(fuel_cost, 1)} ريال
                            </div>
                            <div style="font-size: 1.2em;">سيارة بنزين</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.25); padding: 25px; border-radius: 15px; text-align: center;">
                            <div style="font-size: 4em; margin-bottom: 12px;">⚡</div>
                            <div style="font-size: 2.2em; font-weight: bold; margin-bottom: 8px;">
                                {round(ev_cost, 1)} ريال
                            </div>
                            <div style="font-size: 1.2em;">سيارة كهربائية</div>
                        </div>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                                padding: 25px; border-radius: 15px; text-align: center;">
                        <div style="font-size: 1.3em; margin-bottom: 10px;">💚 التوفير</div>
                        <div style="font-size: 3.5em; font-weight: bold; margin-bottom: 8px;">
                            {round(savings, 1)} ريال
                        </div>
                        <div style="font-size: 1.5em;">({round(savings_pct, 1)}% توفير!)</div>
                    </div>
                </div>
                """
            
            results_html += "</div>" # إغلاق وسم div الرئيسي
            
            display(HTML(results_html))
        
        # Display map
        with self.map_output:
            clear_output(wait=True)
            
            center_lat = (self.start_coords[1] + self.end_coords[1]) / 2
            center_lon = (self.start_coords[0] + self.end_coords[0]) / 2
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='OpenStreetMap')
            plugins.Fullscreen().add_to(m)
            
            # Markers
            folium.Marker(
                [self.start_coords[1], self.start_coords[0]],
                popup=f"<b>🚗 البداية</b><br>{self.start_address[:80]}",
                tooltip="🚗 نقطة البداية",
                icon=folium.Icon(color='green', icon='car', prefix='fa')
            ).add_to(m)
            
            folium.Marker(
                [self.end_coords[1], self.end_coords[0]],
                popup=f"<b>🏁 الوجهة</b><br>{self.end_address[:80]}",
                tooltip="🏁 الوجهة النهائية",
                icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
            ).add_to(m)
            
            # Route sections
            route_coords = self.route_data['coordinates']
            sections = divide_route_into_sections(route_coords, 3)
            colors = ['blue', 'orange', 'purple']
            names = ['القسم 1', 'القسم 2', 'القسم 3']
            
            for i, section in enumerate(sections):
                route_latlon = [[coord[1], coord[0]] for coord in section]
                folium.PolyLine(
                    route_latlon,
                    color=colors[i],
                    weight=7,
                    opacity=0.8,
                    popup=f"{names[i]}<br>~{round(leg_distance, 1)} كم"
                ).add_to(m)
                
                if i < 2:
                    charging_coord = section[-1]
                    if i == 0:
                        point_name = "⚡ محطة A"
                        point_color = cp1_color
                        point_status = cp1_status
                        dist = leg_distance
                    else:
                        point_name = "⚡ محطة B"
                        point_color = cp2_color
                        point_status = cp2_status
                        dist = leg_distance * 2
                    
                    folium.Marker(
                        [charging_coord[1], charging_coord[0]],
                        popup=f"<b>{point_name}</b><br>الحالة: {point_status}<br>المسافة: {round(dist,1)} كم",
                        tooltip=f"{point_name} - {point_status}",
                        icon=folium.Icon(color=point_color, icon='bolt', prefix='fa')
                    ).add_to(m)
            
            m.fit_bounds([[self.start_coords[1], self.start_coords[0]], 
                         [self.end_coords[1], self.end_coords[0]]])
            
            display(m)
    
    def display(self):
        """Display the complete interface (V11 UI)"""
        
        # Header (V11)
        display(HTML("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 40px; border-radius: 25px; color: white; text-align: center; 
                        margin-bottom: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.3);">
                <h1 style="margin: 0; font-size: 3.2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                    🚗⚡ مخطط طريق السيارات الكهربائية
                </h1>
                <h2 style="margin: 12px 0; font-size: 2.3em;">EV Route Planner</h2>
                <p style="margin: 15px 0 0 0; font-size: 1.4em; opacity: 0.95;">
                    V21 - (V11 Repaired)
                </p>
                <p style="margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9;">
                    ✨ فقط انقر مرتين على الخريطة - باقي كل شيء تلقائي!
                </p>
            </div>
        """))
        
        # Main interactive map (V11)
        m = folium.Map(location=[24.7136, 46.6753], zoom_start=6, tiles='OpenStreetMap')
        plugins.Fullscreen().add_to(m)
        
        # --- (((( هذا هو الإصلاح V21 )))) ---
        # --- (تعديل كود JS المحقون) ---
        
        # (نفس كود V11 HTML)
        control_html = """
        <div id="control-panel" style="position: fixed; top: 10px; left: 60px; z-index: 9999; 
                                        background: white; padding: 22px; border-radius: 18px; 
                                        box-shadow: 0 8px 30px rgba(0,0,0,0.4); width: 420px;">
            <h2 style="margin: 0 0 18px 0; color: #667eea; text-align: center; font-size: 1.5em;">
                🗺️ حدد مسارك / Select Route
            </h2>
            
            <div id="mode-indicator" style="padding: 14px; background: #9E9E9E; color: white; 
                                             border-radius: 10px; text-align: center; font-weight: bold; 
                                             margin-bottom: 15px; font-size: 14px;">
                ⚪ اضغط على زر البداية أو النهاية
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 18px;">
                <button onclick="setStartMode()" id="start-btn"
                        style="padding: 15px; background: #4CAF50; color: white; border: none; 
                               border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 14px;
                               box-shadow: 0 4px 12px rgba(76,175,80,0.3); transition: all 0.3s;">
                    🟢 البداية<br><span style="font-size: 12px;">START</span>
                </button>
                <button onclick="setEndMode()" id="end-btn"
                        style="padding: 15px; background: #f44336; color: white; border: none; 
                               border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 14px;
                               box-shadow: 0 4px 12px rgba(244,67,54,0.3); transition: all 0.3s;">
                    🔴 النهاية<br><span style="font-size: 12px;">END</span>
                </button>
            </div>
            
            <div style="background: #f8f9fa; padding: 14px; border-radius: 10px; margin-bottom: 15px;">
                <div id="start-display" style="margin-bottom: 10px; padding: 12px; background: white; 
                                               border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <div style="font-size: 11px; color: #666; margin-bottom: 4px;">نقطة البداية / START</div>
                    <div style="font-size: 13px; color: #333; font-weight: 500;">📍 غير محدد</div>
                </div>
                <div id="end-display" style="padding: 12px; background: white; border-radius: 8px; 
                                            border-left: 4px solid #f44336;">
                    <div style="font-size: 11px; color: #666; margin-bottom: 4px;">نقطة النهاية / END</div>
                    <div style="font-size: 13px; color: #333; font-weight: 500;">🏁 غير محدد</div>
                </div>
            </div>
            
            <button onclick="clearAll()" 
                    style="width: 100%; padding: 12px; background: #ff9800; color: white; border: none; 
                           border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 13px;
                           box-shadow: 0 4px 12px rgba(255,152,0,0.3);">
                🔄 إعادة تعيين / RESET
            </button>
            
            <div style="margin-top: 15px; padding: 12px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                        border-radius: 8px; font-size: 12px; color: #1976D2; line-height: 1.6;">
                <strong>💡 كيف تستخدم:</strong><br>
                1️⃣ اضغط على "البداية 🟢"<br>
                2️⃣ انقر على الخريطة<br>
                3️⃣ اضغط على "النهاية 🔴"<br>
                4️⃣ انقر على الخريطة<br>
                5️⃣ كل شيء آخر تلقائي! ✨
            </div>
        </div>
        
        <script>
        // --- (نفس كود JS من V11، مع تعديل الاستدعاء) ---
        var clickMode = null;
        var startMarker = null;
        var endMarker = null;
        var startCoords = null;
        var endCoords = null;
        var mapObj = null;
        
        function setStartMode() {
            clickMode = 'start';
            document.getElementById('mode-indicator').innerHTML = 
                '🟢 انقر على الخريطة لتحديد نقطة البداية';
            document.getElementById('mode-indicator').style.background = '#4CAF50';
            document.getElementById('start-btn').style.transform = 'scale(1.05)';
            document.getElementById('end-btn').style.transform = 'scale(1)';
        }
        
        function setEndMode() {
            clickMode = 'end';
            document.getElementById('mode-indicator').innerHTML = 
                '🔴 انقر على الخريطة لتحديد نقطة النهاية';
            document.getElementById('mode-indicator').style.background = '#f44336';
            document.getElementById('end-btn').style.transform = 'scale(1.05)';
            document.getElementById('start-btn').style.transform = 'scale(1)';
        }
        
        function clearAll() {
            if (startMarker) mapObj.removeLayer(startMarker);
            if (endMarker) mapObj.removeLayer(endMarker);
            startCoords = null;
            endCoords = null;
            clickMode = null;
            
            document.getElementById('start-display').innerHTML = 
                '<div style="font-size: 11px; color: #666; margin-bottom: 4px;">نقطة البداية / START</div>' +
                '<div style="font-size: 13px; color: #333; font-weight: 500;">📍 غير محدد</div>';
            document.getElementById('end-display').innerHTML = 
                '<div style="font-size: 11px; color: #666; margin-bottom: 4px;">نقطة النهاية / END</div>' +
                '<div style="font-size: 13px; color: #333; font-weight: 500;">🏁 غير محدد</div>';
            document.getElementById('mode-indicator').innerHTML = '⚪ اضغط على زر البداية أو النهاية';
            document.getElementById('mode-indicator').style.background = '#9E9E9E';
            document.getElementById('start-btn').style.transform = 'scale(1)';
            document.getElementById('end-btn').style.transform = 'scale(1)';
            
            // استدعاء بايثون لـ "clear" (اختياري، لكنه جيد)
            // (تم حذفه للتبسيط، clearAll الآن مجرد JS)
        }
        
        function handleMapClick(lat, lng) {
            if (!clickMode) {
                alert('⚠️ الرجاء اختيار وضع البداية أو النهاية أولاً!\\nPlease select START or END mode first!');
                return;
            }
            
            if (clickMode === 'start') {
                startCoords = {lat: lat, lng: lng};
                if (startMarker) mapObj.removeLayer(startMarker);
                
                var greenIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                    iconSize: [25, 41], iconAnchor: [12, 41], shadowSize: [41, 41]
                });
                
                startMarker = L.marker([lat, lng], {icon: greenIcon})
                    .addTo(mapObj).bindPopup('🚗 البداية / START').openPopup();
                
                document.getElementById('start-display').innerHTML = 
                    '<div style="font-size: 11px; color: #666; margin-bottom: 4px;">نقطة البداية / START</div>' +
                    '<div style="font-size: 13px; color: #333; font-weight: 500;">📍 ' + 
                    lat.toFixed(5) + ', ' + lng.toFixed(5) + '</div>';
                
                setTimeout(() => { if (!endCoords) setEndMode(); }, 600);
                
            } else if (clickMode === 'end') {
                endCoords = {lat: lat, lng: lng};
                if (endMarker) mapObj.removeLayer(endMarker);
                
                var redIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                    iconSize: [25, 41], iconAnchor: [12, 41], shadowSize: [41, 41]
                });
                
                endMarker = L.marker([lat, lng], {icon: redIcon})
                    .addTo(mapObj).bindPopup('🏁 النهاية / END').openPopup();
                
                document.getElementById('end-display').innerHTML = 
                    '<div style="font-size: 11px; color: #666; margin-bottom: 4px;">نقطة النهاية / END</div>' +
                    '<div style="font-size: 13px; color: #333; font-weight: 500;">🏁 ' + 
                    lat.toFixed(5) + ', ' + lng.toFixed(5) + '</div>';
                
                clickMode = null;
                document.getElementById('mode-indicator').innerHTML = 
                    '✅ تم! جاري معالجة المسار تلقائياً...';
                document.getElementById('mode-indicator').style.background = '#2196F3';
                document.getElementById('start-btn').style.transform = 'scale(1)';
                document.getElementById('end-btn').style.transform = 'scale(1)';
                
                // Trigger automatic processing
                if (startCoords && endCoords) {
                    
                    // --- ((((((((((( الإصلاح V21 هنا ))))))))))) ---
                    // استبدال (window.pythonCallback) بـ (window.parent.google.colab.backend.rpc.call)
                    window.parent.google.colab.backend.rpc.call(
                        'pythonCallbackV21', // الاسم المسجل في بايثون
                        [startCoords.lat, startCoords.lng, endCoords.lat, endCoords.lng], // الوسائط كـ List
                        {} // kwargs
                    ).then((result) => {
                        console.log('Python callback result (V21):', result); 
                    });
                    // --- ((((((((((( نهاية الإصلاح ))))))))))) ---
                }
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                for (var key in window) {
                    if (window[key] instanceof L.Map) {
                        mapObj = window[key];
                        mapObj.on('click', function(e) {
                            handleMapClick(e.latlng.lat, e.latlng.lng);
                        });
                        break;
                    }
                }
            }, 1500); // 1.5 sec delay
        });
        </script>
        """
        
        m.get_root().html.add_child(folium.Element(control_html))
        
        # (V11 لم يكن لديه <script> ثاني، لذلك لا حاجة لحذفه)
        
        display(m)
        
        # Status output
        display(self.status_output)
        
        # EV Parameters section (V11)
        display(HTML("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 30px; border-radius: 20px; margin: 30px 0;">
                <h2 style="color: white; text-align: center; margin: 0 0 15px 0; font-size: 1.9em;">
                    🔋 معاملات السيارة الكهربائية / EV Parameters
                </h2>
                <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 10px; 
                            margin-bottom: 20px; text-align: center; font-size: 14px; color: white;">
                    ✨ النتائج تتحدث تلقائياً عند تغيير أي قيمة!<br>
                    Results update automatically when you change any value!
                </div>
        """))
        
        params_box = widgets.VBox([
            self.start_soc,
            self.battery_capacity,
            self.ev_efficiency,
            self.fuel_consumption
        ], layout=widgets.Layout(
            padding='25px',
            background='white',
            border_radius='15px',
            width='550px',
            margin='0 auto',
            align_items='center'
        ))
        
        display(params_box)
        display(HTML("</div>"))
        
        # Results section
        display(HTML("""
            <div id="results-section" style="margin: 30px 0;">
                <h2 style="color: #667eea; text-align: center; font-size: 2.3em; margin-bottom: 25px;">
                    📊 النتائج التلقائية / Automatic Results
                </h2>
            </div>
        """))
        
        display(self.results_output)
        
        # Map section
        display(HTML("""
            <div id="map-section" style="margin: 30px 0;">
                <h2 style="color: #667eea; text-align: center; font-size: 2.3em; margin-bottom: 25px;">
                    🗺️ الخريطة التفصيلية / Detailed Map
                </h2>
            </div>
        """))
        
        display(self.map_output)
        
        # (حذف زر الإدخال اليدوي من V11)


# --- (((( هذا هو كود تشغيل V21 )))) ---
# --- (يستخدم google.colab.output) ---

print("🚀 جاري تحميل النظام التلقائي الكامل (V21 - V11 Repaired)...")

# 1. إنشاء نسخة من الكلاس
app = FullyAutomaticEVPlanner()

# 2. تعريف "الدالة الوسيطة"
def colab_js_callback_v21(startLat, startLon, endLat, endLon):
    """This function is registered in Colab's kernel and called by JS"""
    try:
        # استدعاء الدالة الحقيقية داخل الكائن
        result_json = app.process_route(startLat, startLon, endLat, endLon)
        return result_json # إرجاع النتيجة لـ .then() في JS
    except Exception as e:
        print(f"Error in callback (V21): {e}") # طباعة الخطأ في بايثون
        return json.dumps({'status': 'error', 'message': str(e)})

# 3. تسجيل الدالة الوسيطة باستخدام (output.register_callback)
#    (الاسم يطابق الاسم في JS)
output.register_callback('pythonCallbackV21', colab_js_callback_v21)

# 4. عرض الواجهة
app.display()

print("\n" + "="*60)
print("✅ النظام جاهز بالكامل! (V21) / System Fully Ready!")
print("="*60)
print("   هذا هو الكود V11 الأصلي مع إصلاح جسر الاتصال الخاص بـ Colab.")
print("   الرجاء المحاولة الآن.")
print("="*60)
