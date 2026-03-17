from flask import Flask, request, jsonify, render_template_string
from rembg import remove, new_session
import base64

app = Flask(__name__)

# AI Modelleri için oturum (session) önbelleği
ai_sessions = {}

HTML_SAYFASI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AI Arka Plan Temizleyici PRO</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Çoklu indirme (ZIP) için kütüphane -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    
    <style>
        :root {
            --bg-color: #f0f2f5;
            --surface: #ffffff;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --text-dark: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --workspace-bg: #1e1e1e;
            --radius-lg: 16px;
            --radius-md: 10px;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; touch-action: manipulation; }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-color); 
            color: var(--text-dark);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Navbar */
        .navbar {
            background: var(--surface);
            padding: 12px 20px;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
        }
        .logo { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px;}
        .logo span { color: var(--primary); }
        .nav-actions { display: flex; align-items: center; gap: 10px; }

        .btn { padding: 10px 16px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: 0.2s; border: none; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-light { background: #f1f5f9; color: var(--text-dark); }
        .btn-light:hover { background: #e2e8f0; }
        .btn-primary { background: var(--text-dark); color: white; width: 100%;}
        .btn-primary:hover { background: #0f172a; }
        .btn-success { background: #10b981; color: white; width: 100%; }
        .btn-success:hover { background: #059669; }
        .btn-zip { background: var(--primary); color: white; width: 100%; margin-top: 10px;}
        .btn-zip:hover { background: var(--primary-hover); }

        /* Main Layout */
        .app-container {
            display: flex;
            flex-direction: column;
            flex: 1;
            height: calc(100vh - 60px);
            overflow: hidden;
        }

        .workspace-content {
            display: flex;
            flex: 1;
            overflow: hidden;
            position: relative;
        }

        /* YÜKLEME EKRANI (Aşama 1) */
        .upload-view {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            background: var(--bg-color);
            position: absolute;
            top: 60px; left: 0; right: 0; bottom: 0;
            z-index: 50;
        }
        .hero-title { font-size: 42px; font-weight: 800; margin-bottom: 12px; letter-spacing: -1px; text-align: center; padding: 0 20px;}
        .drop-zone {
            background: var(--surface);
            border: 2px dashed #cbd5e1;
            border-radius: 24px;
            padding: 60px 80px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            box-shadow: var(--shadow-md);
            margin-top: 30px;
            max-width: 90%;
        }
        .drop-zone:hover, .drop-zone.dragover { border-color: var(--primary); background: #eff6ff; transform: translateY(-2px); }
        .upload-btn-main {
            background: var(--primary); color: white; padding: 14px 32px; border-radius: 50px;
            font-size: 16px; font-weight: 600; display: inline-block; pointer-events: none;
            box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.3); margin: 15px 0;
        }

        /* ÇALIŞMA ALANI (Aşama 2) */
        .workspace-view { display: none; }

        /* Left Toolbar */
        .toolbar-left {
            width: 80px;
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px 0;
            gap: 12px;
            z-index: 10;
            overflow-y: auto;
        }
        .tool-btn {
            width: 44px; height: 44px; flex-shrink: 0;
            border-radius: 12px;
            display: flex; justify-content: center; align-items: center;
            cursor: pointer; border: none; background: transparent;
            color: var(--text-muted); transition: 0.2s;
        }
        .tool-btn:hover { background: #f1f5f9; color: var(--text-dark); }
        .tool-btn.active { background: #eff6ff; color: var(--primary); box-shadow: inset 0 0 0 1px var(--primary); }
        .tool-divider { width: 40px; height: 1px; background: var(--border); margin: 5px 0; flex-shrink: 0;}
        
        .tool-settings {
            width: 100%; padding: 15px 10px; border-top: 1px solid var(--border);
            display: flex; flex-direction: column; align-items: center; gap: 8px;
            margin-top: auto; background: #fafafa;
        }
        .tool-settings label { font-size: 10px; font-weight: 700; text-align: center; color: var(--text-muted); text-transform: uppercase;}
        .tool-settings span.val { color: var(--primary); font-size: 12px; }
        input[type="range"] { accent-color: var(--primary); cursor: pointer; width: 100%; margin-bottom: 5px; }

        /* Center Viewport */
        .viewport {
            flex: 1;
            background: var(--workspace-bg);
            position: relative;
            overflow: hidden;
            touch-action: none; /* Mobilde kaydırmayı engelle */
        }

        .canvas-wrapper {
            position: absolute;
            top: 0; left: 0;
            transform-origin: 0 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        .checkerboard {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(45deg, #cccccc 25%, transparent 25%), linear-gradient(-45deg, #cccccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #cccccc 75%), linear-gradient(-45deg, transparent 75%, #cccccc 75%);
            background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px; background-color: #ffffff;
            z-index: 1;
        }
        
        #resultCanvas {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 2; display: block; touch-action: none;
        }

        .top-layer {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 3; pointer-events: none;
            clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
        }
        .top-layer img { width: 100%; height: 100%; display: block; object-fit: contain; pointer-events: none; }

        .slider-ui-container {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
            padding: 8px 16px; border-radius: 50px; display: flex; align-items: center; gap: 15px;
            z-index: 20; color: white; font-size: 12px; font-weight: 600;
        }
        .slider-ui-container input { width: 120px; }

        /* Custom Brush Cursor */
        #brushCursor {
            position: fixed;
            border: 1.5px solid rgba(255,255,255,0.9);
            box-shadow: 0 0 0 1px rgba(0,0,0,0.5), inset 0 0 4px rgba(0,0,0,0.3);
            border-radius: 50%; pointer-events: none;
            transform: translate(-50%, -50%);
            display: none; z-index: 9999;
        }

        /* Right Settings Panel */
        .sidebar-right {
            width: 320px;
            background: var(--surface);
            border-left: 1px solid var(--border);
            display: flex; flex-direction: column; z-index: 10;
        }
        .panel-header { padding: 15px 20px; border-bottom: 1px solid var(--border); font-weight: 700; display: flex; align-items: center; justify-content: space-between;}
        .panel-content { padding: 20px; flex: 1; overflow-y: auto; }
        
        .control-group { margin-bottom: 15px; }
        .control-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--text-dark); }
        .control-group select, .control-group input[type="text"] { 
            width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--border); 
            background: var(--bg-color); font-family: inherit; font-size: 13px; outline: none; 
        }

        .range-wrapper { margin-bottom: 12px; }
        .range-label { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; font-weight: 500;}
        .range-wrapper input[type=range] { width: 100%; height: 6px; border-radius: 3px; background: #e2e8f0; outline: none; -webkit-appearance: none;}
        .range-wrapper input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%; background: var(--primary); cursor: pointer;}

        .toggle-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);}
        .toggle-row label { margin: 0; font-size: 13px; cursor: pointer; font-weight: 600;}
        .switch { position: relative; display: inline-block; width: 40px; height: 22px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider-round { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #cbd5e1; transition: .3s; border-radius: 34px; }
        .slider-round:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%;}
        input:checked + .slider-round { background-color: var(--primary); }
        input:checked + .slider-round:before { transform: translateX(18px); }

        /* Gallery Thumbnail Area */
        .gallery-container {
            height: 90px;
            background: var(--surface);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 20px;
            gap: 12px;
            overflow-x: auto;
            z-index: 10;
        }
        .gallery-thumb {
            width: 60px; height: 60px;
            border-radius: 8px;
            object-fit: cover;
            cursor: pointer;
            border: 2px solid transparent;
            opacity: 0.5;
            transition: 0.2s;
            flex-shrink: 0;
            background: #e2e8f0;
        }
        .gallery-thumb:hover { opacity: 0.8; }
        .gallery-thumb.active { border-color: var(--primary); opacity: 1; box-shadow: 0 4px 10px rgba(37,99,235,0.3);}

        .loading-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(30, 30, 30, 0.8); backdrop-filter: blur(4px);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            z-index: 50; display: none; color: white;
        }
        .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 15px;}
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* Mobile View Styles */
        #mobileSettingsBtn { display: none; }
        #closeSidebarBtn { display: none; background: transparent; border: none; font-size: 24px; cursor: pointer; color: var(--text-dark);}

        @media (max-width: 768px) {
            .hero-title { font-size: 28px; }
            .drop-zone { padding: 40px 20px; }
            #mobileSettingsBtn { display: inline-flex; }
            #closeSidebarBtn { display: block; }
            
            .workspace-content { flex-direction: column; }
            .toolbar-left { width: 100%; height: 60px; flex-direction: row; border-right: none; border-bottom: 1px solid var(--border); padding: 0 10px; overflow-x: auto;}
            .tool-divider { width: 1px; height: 30px; margin: 0 5px; }
            .tool-settings { position: absolute; top: 60px; left: 0; width: 100%; flex-direction: row; border-top: none; border-bottom: 1px solid var(--border); z-index: 20; box-shadow: 0 4px 6px rgba(0,0,0,0.05); justify-content: center; height: 50px;}
            .tool-settings label { margin-right: 10px; text-align: left;}
            .tool-settings input[type="range"] { width: 100px; margin: 0;}

            .sidebar-right {
                position: fixed; top: 60px; right: -100%; height: calc(100vh - 60px); width: 85%; max-width: 320px;
                transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: -5px 0 20px rgba(0,0,0,0.15);
            }
            .sidebar-right.open { right: 0; }
            
            .gallery-container { height: 80px; padding: 0 10px; }
            .gallery-thumb { width: 50px; height: 50px; }
            
            .slider-ui-container { bottom: 10px; font-size: 10px; padding: 5px 12px; }
            .slider-ui-container input { width: 80px; }
        }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary)"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
            Remove<span>PRO</span>
        </div>
        <div class="nav-actions">
            <button id="mobileSettingsBtn" class="btn btn-light">Ayarlar</button>
            <label class="btn btn-light" style="margin: 0;">
                Görsel Ekle
                <input type="file" id="imageInputNav" multiple accept="image/png, image/jpeg, image/jpg, image/webp" style="display:none;">
            </label>
        </div>
    </nav>

    <!-- AŞAMA 1: YÜKLEME ALANI -->
    <div id="uploadView" class="upload-view">
        <h1 class="hero-title">Kusursuz Arka Plan Temizliği.</h1>
        <p style="color: var(--text-muted); margin-bottom: 20px; text-align: center; padding: 0 10px;">Toplu yükle, yapay zeka ile sil, fırça ile onar, yüksek kalitede indir.</p>
        
        <div class="drop-zone" id="dropZone">
            <svg style="width:64px; height:64px; color:var(--primary); margin-bottom:15px;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
            <br>
            <div class="upload-btn-main">Fotoğrafları Yükle</div>
            <p style="font-size: 14px; color: var(--text-muted);">veya buraya sürükleyip bırakın</p>
            <input type="file" id="imageInput" multiple accept="image/png, image/jpeg, image/jpg, image/webp" style="display:none;">
        </div>
    </div>

    <!-- AŞAMA 2: ÇALIŞMA ALANI -->
    <div id="workspaceView" class="app-container workspace-view">
        
        <div class="workspace-content">
            <!-- Sol Araç Kutusu -->
            <div class="toolbar-left">
                <!-- Undo / Redo -->
                <button class="tool-btn" id="toolUndo" title="Geri Al (Ctrl+Z)">
                    <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/></svg>
                </button>
                <button class="tool-btn" id="toolRedo" title="İleri Al (Ctrl+Y)">
                    <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"/></svg>
                </button>
                <div class="tool-divider"></div>

                <button class="tool-btn active" id="toolPan" title="Pan (El) Aracı - Resmi Kaydır">
                    <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M14 10.5V5a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M10 10.5V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M6 14v-2a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8a10 10 0 0 0 10 10h1a10 10 0 0 0 10-10V14a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/></svg>
                </button>
                <button class="tool-btn" id="toolErase" title="Silgi Aracı (Yumuşak Fırça)">
                    <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m7 21-4.3-4.3a2 2 0 0 1 0-2.8l11.3-11.3a2 2 0 0 1 2.8 0l2.9 2.9a2 2 0 0 1 0 2.8L8.4 19.6Z"/><path d="m15.6 2.8 5.6 5.6"/><path d="M22 21H7"/></svg>
                </button>
                <!-- Yeni Araç: Fırça ile Geri Getirme (Restore) -->
                <button class="tool-btn" id="toolRestore" title="Orijinali Geri Getir Fırçası">
                    <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg>
                </button>
                
                <button class="tool-btn" id="toolMagic" title="Sihirli Silgi (Renk Temizleyici)">
                    <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
                    </svg>
                </button>
                <div class="tool-divider"></div>
                <button class="tool-btn" id="toolFit" title="Ekrana Sığdır">
                    <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg>
                </button>
                
                <div style="flex-grow: 1;"></div>
                
                <!-- Dinamik Araç Ayarları -->
                <div class="tool-settings" id="settingsBrush" style="display: none;">
                    <label>Boyut <span class="val" id="sizeVal">40</span></label>
                    <input type="range" id="brushSize" min="1" max="250" value="40">
                    <div style="height:5px;" class="mobile-hide"></div>
                    <label>Sertlik <span class="val"><span id="hardnessVal">50</span>%</span></label>
                    <input type="range" id="brushHardness" min="0" max="100" value="50">
                </div>

                <div class="tool-settings" id="settingsMagic" style="display: none;">
                    <label>Tolerans <span class="val" id="magicVal">40</span></label>
                    <input type="range" id="magicTolerance" min="1" max="150" value="40">
                </div>
            </div>

            <!-- Merkez Görüntü (Viewport) -->
            <div class="viewport" id="viewport">
                <div class="loading-overlay" id="loadingOverlay">
                    <div class="spinner"></div>
                    <div style="font-weight: 600;" id="loadingText">İşleniyor...</div>
                </div>

                <div id="brushCursor"></div>

                <div class="canvas-wrapper" id="canvasWrapper">
                    <div class="checkerboard"></div>
                    <canvas id="resultCanvas"></canvas>
                    <div class="top-layer" id="topLayer">
                        <img id="originalImg" alt="Original">
                    </div>
                </div>

                <div class="slider-ui-container">
                    <span>Sonuç</span>
                    <input type="range" id="compareSlider" min="0" max="100" value="100">
                    <span>Orijinal</span>
                </div>
            </div>

            <!-- Sağ Ayarlar Paneli -->
            <div class="sidebar-right" id="sidebarRight">
                <div class="panel-header">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 20V10M18 20V4M6 20v-4"/></svg> 
                        İnce Ayarlar
                    </div>
                    <button id="closeSidebarBtn">&times;</button>
                </div>
                
                <div class="panel-content">
                    <div class="control-group">
                        <label>Yapay Zeka Modeli</label>
                        <select id="modelSelect">
                            <option value="u2net">U²-Net (Genel / Tavsiye Edilen)</option>
                            <option value="isnet-general-use">IS-Net (Detaylı Objeler)</option>
                            <option value="u2net_human_seg">Sadece İnsan Figürü</option>
                        </select>
                    </div>

                    <div class="toggle-row">
                        <label for="useMatting">Hassas Kenar (Saç) Modu</label>
                        <label class="switch">
                            <input type="checkbox" id="useMatting" checked>
                            <span class="slider-round"></span>
                        </label>
                    </div>
                    
                    <div id="mattingSettings">
                        <div class="range-wrapper">
                            <div class="range-label"><span>Ön Plan Koruma</span> <span id="fgVal">240</span></div>
                            <input type="range" id="fgThreshold" min="0" max="255" value="240">
                        </div>
                        <div class="range-wrapper">
                            <div class="range-label"><span>Arka Plan Temizliği</span> <span id="bgVal">10</span></div>
                            <input type="range" id="bgThreshold" min="0" max="255" value="10">
                        </div>
                        <div class="range-wrapper">
                            <div class="range-label"><span>Kenar Daraltma</span> <span id="erodeVal">10</span></div>
                            <input type="range" id="erodeSize" min="0" max="50" value="10">
                        </div>
                    </div>

                    <button id="recalcBtn" class="btn btn-primary">
                        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 2v6h-6M3 12a9 9 0 1 0 2.63-6.37L2 8M3 22v-6h6M21 12a9 9 0 1 0-2.63 6.37L22 16"/></svg>
                        Seçili Görsele Yapay Zeka Uygula
                    </button>

                    <hr style="border:0; border-top:1px solid var(--border); margin: 25px 0;">

                    <div class="control-group">
                        <label>Dışa Aktarma Formatı</label>
                        <select id="downloadFormat">
                            <option value="PNG">PNG (Şeffaf Arka Plan)</option>
                            <option value="JPG">JPG (Beyaz Arka Plan)</option>
                        </select>
                    </div>

                    <button id="downloadBtn" class="btn btn-success">
                        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                        Aktif Olanı İndir
                    </button>

                    <button id="downloadZipBtn" class="btn btn-zip">
                        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/><path d="M12 3v12"/></svg>
                        Tüm İşlenenleri İndir (ZIP)
                    </button>
                    
                    <div style="margin-top: 20px; font-size: 11px; color: var(--text-muted); background: #f8fafc; padding: 10px; border-radius: 8px;">
                        <strong>İpuçları:</strong><br><br>
                        • Fırça Boyutu: <kbd>[</kbd> ve <kbd>]</kbd><br>
                        • İşlemi Geri Al: <kbd>Ctrl</kbd> + <kbd>Z</kbd><br>
                        • Fırça Geri Getir (Restore): Yapay zekanın yanlış sildiği kısımları orijinal görselden boyayarak geri getirir.
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alt Galeri (Çoklu Görseller İçin) -->
        <div id="galleryContainer" class="gallery-container">
            <!-- JavaScript tarafından küçük resimler buraya eklenecek -->
        </div>

    </div>

    <script>
        // DOM Elements
        const uploadView = document.getElementById('uploadView');
        const workspaceView = document.getElementById('workspaceView');
        const dropZone = document.getElementById('dropZone');
        const fileInputs =[document.getElementById('imageInput'), document.getElementById('imageInputNav')];
        
        const loadingOverlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        const galleryContainer = document.getElementById('galleryContainer');
        
        // Canvas & Viewport Elements
        const viewport = document.getElementById('viewport');
        const canvasWrapper = document.getElementById('canvasWrapper');
        const canvas = document.getElementById('resultCanvas');
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        const originalImg = document.getElementById('originalImg');
        const topLayer = document.getElementById('topLayer');
        const compareSlider = document.getElementById('compareSlider');
        
        // Tools & UI
        const tools = {
            pan: document.getElementById('toolPan'),
            erase: document.getElementById('toolErase'),
            restore: document.getElementById('toolRestore'),
            magic: document.getElementById('toolMagic')
        };
        const btnUndo = document.getElementById('toolUndo');
        const btnRedo = document.getElementById('toolRedo');
        const toolFit = document.getElementById('toolFit');
        const settingsBrush = document.getElementById('settingsBrush');
        const settingsMagic = document.getElementById('settingsMagic');
        
        const brushSizeInput = document.getElementById('brushSize');
        const brushHardnessInput = document.getElementById('brushHardness');
        const magicToleranceInput = document.getElementById('magicTolerance');
        const brushCursor = document.getElementById('brushCursor');
        
        const sidebarRight = document.getElementById('sidebarRight');
        const mobileSettingsBtn = document.getElementById('mobileSettingsBtn');
        const closeSidebarBtn = document.getElementById('closeSidebarBtn');

        // State & Data Management
        let images = [];       // { id, file, origURL, width, height, history:[], historyIndex: -1, isProcessing }
        let activeId = null;   // Şu an ekrandaki görsel
        
        let currentTool = 'pan'; 
        let scale = 1;
        let panX = 0, panY = 0;
        let isDragging = false;
        let startX, startY;
        let lastDrawX, lastDrawY;

        // UI Listeners (Settings)
        const useMatting = document.getElementById('useMatting');
        const mattingSettings = document.getElementById('mattingSettings');
        useMatting.addEventListener('change', (e) => {
            mattingSettings.style.opacity = e.target.checked ? "1" : "0.5";
            mattingSettings.style.pointerEvents = e.target.checked ? "auto" : "none";
        });
        
        document.getElementById('fgThreshold').addEventListener('input', e => document.getElementById('fgVal').innerText = e.target.value);
        document.getElementById('bgThreshold').addEventListener('input', e => document.getElementById('bgVal').innerText = e.target.value);
        document.getElementById('erodeSize').addEventListener('input', e => document.getElementById('erodeVal').innerText = e.target.value);
        
        brushSizeInput.addEventListener('input', e => { document.getElementById('sizeVal').innerText = e.target.value; updateBrushCursorScale(); });
        brushHardnessInput.addEventListener('input', e => { document.getElementById('hardnessVal').innerText = e.target.value; updateBrushCursorScale(); });
        magicToleranceInput.addEventListener('input', e => { document.getElementById('magicVal').innerText = e.target.value; });

        mobileSettingsBtn.addEventListener('click', () => sidebarRight.classList.add('open'));
        closeSidebarBtn.addEventListener('click', () => sidebarRight.classList.remove('open'));

        // --- Multi File Upload Mechanics ---
        dropZone.addEventListener('click', () => fileInputs[0].click());
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', e => { e.preventDefault(); dropZone.classList.remove('dragover'); });
        dropZone.addEventListener('drop', e => {
            e.preventDefault(); dropZone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        fileInputs.forEach(input => {
            input.addEventListener('change', function() { handleFiles(this.files); });
        });

        function handleFiles(files) {
            if (!files || files.length === 0) return;
            
            let firstNewId = null;
            Array.from(files).forEach(file => {
                if (!file.type.startsWith('image/')) return;
                const id = 'img_' + Date.now() + Math.floor(Math.random() * 1000);
                const objUrl = URL.createObjectURL(file);
                
                images.push({
                    id: id,
                    file: file,
                    origURL: objUrl,
                    history:[],
                    historyIndex: -1,
                    isProcessing: false,
                    width: 0, height: 0
                });
                
                if(!firstNewId) firstNewId = id;
                createGalleryThumbnail(id, objUrl);
            });

            if (images.length > 0) {
                uploadView.style.display = 'none';
                workspaceView.style.display = 'flex';
                if(firstNewId) selectImage(firstNewId);
            }
        }

        function createGalleryThumbnail(id, src) {
            const img = document.createElement('img');
            img.src = src;
            img.id = 'thumb_' + id;
            img.className = 'gallery-thumb';
            img.addEventListener('click', () => selectImage(id));
            galleryContainer.appendChild(img);
        }

        // --- Image Selection & Rendering ---
        function getActiveObj() { return images.find(i => i.id === activeId); }

        function selectImage(id) {
            activeId = id;
            const imgObj = getActiveObj();
            if(!imgObj) return;

            document.querySelectorAll('.gallery-thumb').forEach(el => el.classList.remove('active'));
            document.getElementById('thumb_' + id).classList.add('active');

            originalImg.src = imgObj.origURL;
            originalImg.onload = () => {
                imgObj.width = originalImg.naturalWidth;
                imgObj.height = originalImg.naturalHeight;
                canvas.width = imgObj.width;
                canvas.height = imgObj.height;
                canvasWrapper.style.width = canvas.width + 'px';
                canvasWrapper.style.height = canvas.height + 'px';

                compareSlider.value = 100; updateSliderUI();

                if (imgObj.history.length > 0) {
                    // Daha önce işlem yapılmış, history'den yükle
                    ctx.putImageData(imgObj.history[imgObj.historyIndex], 0, 0);
                    setTimeout(fitToScreen, 50);
                } else if (!imgObj.isProcessing) {
                    // İlk defa seçiliyor, otomatik arka plan temizle
                    setTimeout(() => {
                        fitToScreen();
                        executeAIProcess();
                    }, 50);
                }
            };
        }

        // --- History (Undo/Redo) System ---
        function saveState() {
            const imgObj = getActiveObj();
            if(!imgObj) return;
            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            // Eğer ileri alınmışken yeni çizim yapılırsa, sonraki geçmişi sil
            imgObj.history = imgObj.history.slice(0, imgObj.historyIndex + 1);
            imgObj.history.push(imgData);
            imgObj.historyIndex++;
        }

        function undo() {
            const imgObj = getActiveObj();
            if (imgObj && imgObj.historyIndex > 0) {
                imgObj.historyIndex--;
                ctx.putImageData(imgObj.history[imgObj.historyIndex], 0, 0);
            }
        }

        function redo() {
            const imgObj = getActiveObj();
            if (imgObj && imgObj.historyIndex < imgObj.history.length - 1) {
                imgObj.historyIndex++;
                ctx.putImageData(imgObj.history[imgObj.historyIndex], 0, 0);
            }
        }

        btnUndo.addEventListener('click', undo);
        btnRedo.addEventListener('click', redo);

        // --- AI Process ---
        async function executeAIProcess() {
            const imgObj = getActiveObj();
            if (!imgObj) return;
            
            loadingText.innerText = "Yapay Zeka İşliyor...";
            loadingOverlay.style.display = 'flex';
            imgObj.isProcessing = true;

            const formData = new FormData();
            formData.append('image', imgObj.file);
            formData.append('model', document.getElementById('modelSelect').value);
            formData.append('use_matting', document.getElementById('useMatting').checked);
            formData.append('fg_threshold', document.getElementById('fgThreshold').value);
            formData.append('bg_threshold', document.getElementById('bgThreshold').value);
            formData.append('erode_size', document.getElementById('erodeSize').value);

            try {
                const response = await fetch('/remove-bg', { method: 'POST', body: formData });
                if(!response.ok) throw new Error('API Hatası');
                const data = await response.json();
                if(data.error) throw new Error(data.error);

                const img = new Image();
                img.onload = () => {
                    ctx.globalCompositeOperation = 'source-over'; 
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0);
                    
                    saveState(); // İlk başarılı durumu kaydet
                    
                    // Slider Animasyonu
                    compareSlider.value = 100; updateSliderUI();
                    let val = 100;
                    const anim = setInterval(() => {
                        val -= 4;
                        if(val <= 0) { clearInterval(anim); compareSlider.value = 0; updateSliderUI(); }
                        else { compareSlider.value = val; updateSliderUI(); }
                    }, 16);
                };
                img.src = "data:image/png;base64," + data.image;

            } catch (err) {
                alert("İşlem Hatası: " + err.message);
            } finally {
                loadingOverlay.style.display = 'none';
                imgObj.isProcessing = false;
            }
        }
        document.getElementById('recalcBtn').addEventListener('click', () => {
            const imgObj = getActiveObj();
            if(imgObj) {
                imgObj.history =[]; // Eski geçmişi sıfırla
                imgObj.historyIndex = -1;
                executeAIProcess();
            }
        });

        // --- Zoom & Pan ---
        function updateTransform() { canvasWrapper.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`; }

        function fitToScreen() {
            const padding = 60;
            const vw = Math.max(100, viewport.clientWidth - padding);
            const vh = Math.max(100, viewport.clientHeight - padding);
            
            const scaleX = vw / canvas.width;
            const scaleY = vh / canvas.height;
            scale = Math.min(scaleX, scaleY);
            if(scale <= 0) scale = 1; 
            
            panX = (viewport.clientWidth - (canvas.width * scale)) / 2;
            panY = (viewport.clientHeight - (canvas.height * scale)) / 2;
            updateTransform();
        }
        toolFit.addEventListener('click', fitToScreen);

        viewport.addEventListener('wheel', (e) => {
            e.preventDefault();
            const rect = viewport.getBoundingClientRect();
            const zoomPointX = e.clientX - rect.left;
            const zoomPointY = e.clientY - rect.top;
            
            const zoomAmount = e.deltaY * -0.0015;
            const newScale = Math.min(Math.max(0.05, scale + zoomAmount), 10);
            
            panX -= (zoomPointX - panX) * (newScale / scale - 1);
            panY -= (zoomPointY - panY) * (newScale / scale - 1);
            
            scale = newScale;
            updateTransform();
            updateBrushCursorScale();
        });

        // --- Tool Selection ---
        Object.keys(tools).forEach(key => {
            tools[key].addEventListener('click', () => setTool(key));
        });

        function setTool(tool) {
            currentTool = tool;
            Object.keys(tools).forEach(k => tools[k].classList.toggle('active', k === tool));
            
            settingsBrush.style.display = (tool === 'erase' || tool === 'restore') ? 'flex' : 'none';
            settingsMagic.style.display = tool === 'magic' ? 'flex' : 'none';

            if (tool === 'pan') viewport.style.cursor = 'grab';
            else if (tool === 'magic') viewport.style.cursor = 'crosshair';
            else viewport.style.cursor = 'none';
            
            brushCursor.style.display = 'none';
        }
        setTool('pan');

        // --- Universal Event Handlers (Mouse + Touch) ---
        const getCoords = (e) => {
            if (e.touches && e.touches.length > 0) return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            return { x: e.clientX, y: e.clientY };
        };

        function startAction(e) {
            if (e.target === compareSlider || !getActiveObj()) return;
            isDragging = true;
            const coords = getCoords(e);
            
            if (currentTool === 'pan') {
                viewport.style.cursor = 'grabbing';
                startX = coords.x - panX;
                startY = coords.y - panY;
            } else if (currentTool === 'erase' || currentTool === 'restore') {
                draw(coords.x, coords.y);
            } else if (currentTool === 'magic') {
                executeMagicWand(coords.x, coords.y);
                isDragging = false;
            }
        }

        function moveAction(e) {
            const coords = getCoords(e);
            
            if (currentTool === 'erase' || currentTool === 'restore') {
                brushCursor.style.display = 'block';
                brushCursor.style.left = coords.x + 'px';
                brushCursor.style.top = coords.y + 'px';
            }

            if (!isDragging) return;

            if (currentTool === 'pan') {
                panX = coords.x - startX;
                panY = coords.y - startY;
                updateTransform();
            } else if (currentTool === 'erase' || currentTool === 'restore') {
                draw(coords.x, coords.y);
            }
        }

        function endAction(e) {
            if (isDragging && (currentTool === 'erase' || currentTool === 'restore')) {
                saveState(); // Çizim bitince history'ye kaydet
            }
            isDragging = false;
            if (currentTool === 'pan') viewport.style.cursor = 'grab';
            lastDrawX = undefined;
            lastDrawY = undefined;
        }

        // Mouse Events
        viewport.addEventListener('mousedown', startAction);
        window.addEventListener('mouseup', endAction);
        viewport.addEventListener('mousemove', moveAction);
        viewport.addEventListener('mouseleave', () => { brushCursor.style.display = 'none'; endAction(); });
        
        // Touch Events
        viewport.addEventListener('touchstart', (e) => { startAction(e); }, {passive: false});
        window.addEventListener('touchend', endAction);
        viewport.addEventListener('touchmove', (e) => { 
            if(isDragging && currentTool !== 'pan') e.preventDefault(); 
            moveAction(e); 
        }, {passive: false});

        // --- Keyboard Shortcuts (Undo/Redo & Brush Size) ---
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'z') { e.preventDefault(); undo(); }
            if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'Z'))) { e.preventDefault(); redo(); }

            if (currentTool === 'erase' || currentTool === 'restore') {
                let size = parseInt(brushSizeInput.value);
                if (e.key === '[' && !e.shiftKey) { brushSizeInput.value = Math.max(1, size - 5); brushSizeInput.dispatchEvent(new Event('input')); }
                if (e.key === ']' && !e.shiftKey) { brushSizeInput.value = Math.min(250, size + 5); brushSizeInput.dispatchEvent(new Event('input')); }
            }
        });

        // --- Draw (Erase & Restore) Logic ---
        function draw(clientX, clientY) {
            const rect = canvas.getBoundingClientRect();
            const x = (clientX - rect.left) / scale;
            const y = (clientY - rect.top) / scale;
            
            const size = parseInt(brushSizeInput.value) / scale;
            const hardness = parseInt(brushHardnessInput.value);
            
            ctx.lineWidth = size;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            if (currentTool === 'erase') {
                const blurPx = (size / 2) * ((100 - hardness) / 100);
                ctx.globalCompositeOperation = 'destination-out';
                ctx.filter = `blur(${blurPx}px)`;

                ctx.beginPath();
                if (lastDrawX === undefined) { ctx.arc(x, y, size / 2, 0, Math.PI * 2); ctx.fill(); } 
                else { ctx.moveTo(lastDrawX, lastDrawY); ctx.lineTo(x, y); ctx.stroke(); }
                ctx.filter = 'none';
            } 
            else if (currentTool === 'restore') {
                // Restore mantığı: Orijinal görseli, fırça çizimiyle maskeleyerek çizeriz.
                ctx.globalCompositeOperation = 'source-over';
                ctx.save();
                ctx.beginPath();
                if (lastDrawX === undefined) {
                    ctx.arc(x, y, size / 2, 0, Math.PI * 2);
                } else {
                    ctx.moveTo(lastDrawX, lastDrawY);
                    ctx.lineTo(x, y);
                }
                ctx.clip(); // Çizilen alanı seç
                ctx.drawImage(originalImg, 0, 0, canvas.width, canvas.height); // Orijinal görseli sadece o alana çiz
                ctx.restore();
            }

            lastDrawX = x; lastDrawY = y;
        }

        // --- Magic Wand ---
        function executeMagicWand(clientX, clientY) {
            const rect = canvas.getBoundingClientRect();
            const startX = Math.floor((clientX - rect.left) / scale);
            const startY = Math.floor((clientY - rect.top) / scale);

            if (startX < 0 || startY < 0 || startX >= canvas.width || startY >= canvas.height) return;

            loadingText.innerText = "Renk Temizleniyor...";
            loadingOverlay.style.display = 'flex';

            setTimeout(() => {
                const tolerance = parseInt(magicToleranceInput.value);
                const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imgData.data;
                const targetIdx = (startY * canvas.width + startX) * 4;
                const targetR = data[targetIdx], targetG = data[targetIdx + 1], targetB = data[targetIdx + 2], targetA = data[targetIdx + 3];
                
                if (targetA !== 0) {
                    for (let i = 0; i < data.length; i += 4) {
                        if (data[i + 3] === 0) continue; 
                        const dr = data[i] - targetR, dg = data[i + 1] - targetG, db = data[i + 2] - targetB;
                        if (Math.sqrt(dr*dr + dg*dg + db*db) <= tolerance) data[i + 3] = 0;
                    }
                    ctx.putImageData(imgData, 0, 0);
                    saveState(); // İşlem bitince kaydet
                }
                loadingOverlay.style.display = 'none';
            }, 50);
        }

        // --- Visual Sync ---
        function updateBrushCursorScale() {
            const size = brushSizeInput.value;
            brushCursor.style.width = size + 'px';
            brushCursor.style.height = size + 'px';
            const hardness = brushHardnessInput.value;
            const blurAmount = (100 - hardness) / 100 * (size / 2);
            brushCursor.style.boxShadow = hardness < 90 
                ? `0 0 0 1px rgba(0,0,0,0.5), inset 0 0 ${blurAmount}px rgba(0,0,0,0.6)`
                : `0 0 0 1px rgba(0,0,0,0.5), inset 0 0 4px rgba(0,0,0,0.3)`;
        }
        updateBrushCursorScale();

        compareSlider.addEventListener('input', updateSliderUI);
        function updateSliderUI() { topLayer.style.clipPath = `polygon(0 0, ${compareSlider.value}% 0, ${compareSlider.value}% 100%, 0 100%)`; }
        originalImg.addEventListener('dragstart', e => e.preventDefault());

        // --- Single Image Download ---
        document.getElementById('downloadBtn').addEventListener('click', () => {
            const imgObj = getActiveObj();
            if(!imgObj || imgObj.history.length === 0) return alert("İndirilecek işlenmiş görsel yok.");
            
            const format = document.getElementById('downloadFormat').value;
            const link = document.createElement('a');
            link.download = `remove_pro_${imgObj.id}.${format.toLowerCase()}`;

            if (format === 'JPG') {
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = canvas.width; tempCanvas.height = canvas.height;
                const tCtx = tempCanvas.getContext('2d');
                tCtx.fillStyle = '#FFFFFF'; tCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
                tCtx.drawImage(canvas, 0, 0);
                link.href = tempCanvas.toDataURL('image/jpeg', 0.95);
            } else {
                link.href = canvas.toDataURL('image/png');
            }
            link.click();
        });

        // --- Batch ZIP Download ---
        document.getElementById('downloadZipBtn').addEventListener('click', async () => {
            const processedImages = images.filter(i => i.history && i.history.length > 0);
            if (processedImages.length === 0) return alert("İndirilecek hiçbir işlenmiş görsel bulunamadı.");
            
            loadingText.innerText = "ZIP Hazırlanıyor...";
            loadingOverlay.style.display = 'flex';

            setTimeout(async () => {
                try {
                    const zip = new JSZip();
                    const format = document.getElementById('downloadFormat').value;
                    
                    for (let i = 0; i < processedImages.length; i++) {
                        const imgObj = processedImages[i];
                        const historyData = imgObj.history[imgObj.historyIndex];
                        
                        // imageData'yı Blob'a çevirmek için geçici canvas kullanıyoruz
                        const tCanvas = document.createElement('canvas');
                        tCanvas.width = historyData.width; tCanvas.height = historyData.height;
                        const tCtx = tCanvas.getContext('2d');
                        
                        if (format === 'JPG') {
                            tCtx.fillStyle = '#FFFFFF';
                            tCtx.fillRect(0, 0, tCanvas.width, tCanvas.height);
                            // Saydam piksellerin altına beyaz atıp ImageData'yı üstüne koyamayız (putImageData alfa kanalını ezer)
                            // Bu yüzden bir ara temp canvas üzerinden çizdirmeliyiz.
                            const intermediate = document.createElement('canvas');
                            intermediate.width = historyData.width; intermediate.height = historyData.height;
                            intermediate.getContext('2d').putImageData(historyData, 0, 0);
                            tCtx.drawImage(intermediate, 0, 0);
                        } else {
                            tCtx.putImageData(historyData, 0, 0);
                        }

                        const blob = await new Promise(resolve => tCanvas.toBlob(resolve, format === 'JPG' ? 'image/jpeg' : 'image/png', 0.95));
                        zip.file(`image_${i+1}.${format.toLowerCase()}`, blob);
                    }

                    const zipBlob = await zip.generateAsync({type:"blob"});
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(zipBlob);
                    link.download = "RemovePRO_Gorseller.zip";
                    link.click();
                } catch (e) {
                    alert("ZIP oluşturulurken hata: " + e.message);
                } finally {
                    loadingOverlay.style.display = 'none';
                }
            }, 50);
        });

    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_SAYFASI)

@app.route('/remove-bg', methods=['POST'])
def remove_bg():
    if 'image' not in request.files:
        return jsonify({'error': 'Sunucuya gönderilmiş resim dosyası bulunamadı.'}), 400
    
    file = request.files['image']
    
    model_name = request.form.get('model', 'u2net')
    use_matting = request.form.get('use_matting') == 'true'
    fg_threshold = int(request.form.get('fg_threshold', 240))
    bg_threshold = int(request.form.get('bg_threshold', 10))
    erode_size = int(request.form.get('erode_size', 10))
    
    try:
        input_image = file.read()
        
        if model_name not in ai_sessions:
            print(f"[{model_name}] modeli hafızaya yükleniyor...")
            ai_sessions[model_name] = new_session(model_name)
        
        session = ai_sessions[model_name]
        
        output_image = remove(
            input_image, 
            session=session, 
            alpha_matting=use_matting,
            alpha_matting_foreground_threshold=fg_threshold,
            alpha_matting_background_threshold=bg_threshold,
            alpha_matting_erode_size=erode_size
        )
        
        base64_encoded = base64.b64encode(output_image).decode('utf-8')
        return jsonify({'image': base64_encoded})
    
    except Exception as e:
        print("\n=== ARKA PLAN SİLME HATASI ===")
        print("Hata Çıktısı:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" ✨ AI ARKA PLAN TEMİZLEYİCİ PRO BAŞLATILDI ✨")
    print(" 🌍 Tarayıcıda açın:  http://127.0.0.1:5000 ")
    print("="*60 + "\n")
    app.run(debug=True, port=5000, host="0.0.0.0")