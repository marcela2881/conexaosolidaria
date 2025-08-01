from flask import Flask, render_template_string, request, redirect, url_for, send_file, flash
import sqlite3
import qrcode
import uuid
from datetime import datetime
import io
import base64
import os
from werkzeug.utils import secure_filename
import requests
PAGBANK_TOKEN = "1979ca21-1ad4-4182-8a8a-adb532730bba6a0f6ac84902b8486821a00c90bc0a836452-7c20-43b0-b4be-867c1d562c4f"
PAGBANK_BASE_URL = "https://api.pagseguro.com"

app = Flask(__name__)
app.secret_key = 'conexao_solidaria_2025'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}

# SUBSTITUA PELOS LINKS REAIS DO WHATSAPP
WHATSAPP_INICIANTE = "https://chat.whatsapp.com/LINK_INICIANTE"
WHATSAPP_INTERMEDIARIO = "https://chat.whatsapp.com/LINK_INTERMEDIARIO"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('conexao_solidaria.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ingressos (
        id TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT,
        idade INTEGER,
        categoria TEXT NOT NULL,
        preco REAL NOT NULL,
        status TEXT DEFAULT 'ativo',
        data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usado BOOLEAN DEFAULT 0,
        data_uso TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS editais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        arquivo TEXT,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ativo BOOLEAN DEFAULT 1
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>I Torneio Beneficente - Conexão Solidária</title>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #9333ea, #e879f9, #f3e8ff);
            min-height: 100vh; 
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }
        
        /* Elementos decorativos de vôlei */
        .volleyball-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            opacity: 0.1;
        }
        
        .volleyball-ball {
            position: absolute;
            font-size: 3em;
            animation: float 6s ease-in-out infinite;
        }
        
        .volleyball-ball:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
        .volleyball-ball:nth-child(2) { top: 20%; right: 15%; animation-delay: 2s; }
        .volleyball-ball:nth-child(3) { bottom: 30%; left: 20%; animation-delay: 4s; }
        .volleyball-ball:nth-child(4) { bottom: 15%; right: 25%; animation-delay: 1s; }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }
        
        .net-decoration {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 2px;
            height: 100%;
            background: repeating-linear-gradient(
                to bottom,
                #9333ea 0px,
                #9333ea 20px,
                transparent 20px,
                transparent 40px
            );
            opacity: 0.1;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 30px;
            padding: 0;
            box-shadow: 0 25px 50px rgba(147, 51, 234, 0.4);
            border: 3px solid #9333ea;
            backdrop-filter: blur(10px);
            overflow: hidden;
        }
        
        .header {
            text-align: center;
            padding: 40px;
            background: linear-gradient(135deg, #9333ea, #7c3aed, #a855f7);
            color: white;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '🏐';
            position: absolute;
            top: 20px;
            left: 30px;
            font-size: 2.5em;
            animation: bounce 2s infinite;
        }
        
        .header::after {
            content: '🥅';
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 2.5em;
            animation: bounce 2s infinite 1s;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .header h1 { 
            font-size: 3.2em; 
            margin-bottom: 15px; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            font-weight: bold;
        }
        
        .header h2 { 
            font-size: 1.8em; 
            margin-bottom: 20px; 
            opacity: 0.95;
        }
        
        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
            margin-top: 10px;
        }
        
        /* Seção do Projeto */
        .project-section {
            padding: 50px 40px;
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            text-align: center;
            border-bottom: 3px solid #e2e8f0;
        }
        
        .project-title {
            color: #9333ea;
            font-size: 2.5em;
            margin-bottom: 30px;
            font-weight: bold;
        }
        
        .photos-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }
        
        .photo-placeholder {
            height: 200px;
            background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4em;
            color: #9333ea;
            border: 3px dashed #9333ea;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .photo-placeholder:hover {
            transform: scale(1.05);
            background: linear-gradient(135deg, #ddd6fe, #c4b5fd);
        }
        
        .project-description {
            background: white;
            padding: 40px;
            border-radius: 20px;
            margin: 30px 0;
            border: 2px solid #9333ea;
            text-align: left;
            line-height: 1.8;
            font-size: 1.1em;
            color: #374151;
        }
        
        .project-description h3 {
            color: #9333ea;
            font-size: 1.8em;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .project-highlights {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .highlight-card {
            background: linear-gradient(135deg, #9333ea, #a855f7);
            color: white;
            padding: 25px;
            border-radius: 20px;
            text-align: center;
        }
        
        .highlight-card .icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .highlight-card h4 {
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        /* Formulário */
        .form-section {
            background: white;
            padding: 40px;
            margin: 0;
        }
        
        .form-section h3 {
            color: #9333ea;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.2em;
        }
        
        .form-group { 
            margin-bottom: 25px; 
        }
        
        .form-group label {
            display: block;
            margin-bottom: 10px;
            font-weight: bold;
            color: #9333ea;
            font-size: 1.2em;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 18px;
            border: 3px solid #e2e8f0;
            border-radius: 15px;
            font-size: 16px;
            background: #f8fafc;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #9333ea;
            background: white;
            box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
        }
        
        .submit-btn {
            background: linear-gradient(135deg, #9333ea, #7c3aed);
            color: white;
            padding: 20px 40px;
            border: none;
            border-radius: 20px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(147, 51, 234, 0.4);
        }
        
        .links-section {
            text-align: center;
            padding: 40px;
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border-top: 3px solid #e2e8f0;
        }
        
        .nav-btn {
            display: inline-block;
            background: white;
            color: #9333ea;
            padding: 18px 30px;
            margin: 10px;
            border: 3px solid #9333ea;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover {
            background: #9333ea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(147, 51, 234, 0.3);
        }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .container { margin: 10px; padding: 0; }
            .header h1 { font-size: 2.2em; }
            .header h2 { font-size: 1.4em; }
            .project-title { font-size: 2em; }
            .form-section, .project-section { padding: 30px 20px; }
            .photos-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <!-- Elementos decorativos de fundo -->
    <div class="volleyball-bg">
        <div class="volleyball-ball">🏐</div>
        <div class="volleyball-ball">🥅</div>
        <div class="volleyball-ball">🏐</div>
        <div class="volleyball-ball">🥅</div>
        <div class="net-decoration"></div>
    </div>

    <div class="container">
        <!-- Cabeçalho -->
        <div class="header">
            <h1>🏐 I TORNEIO BENEFICENTE</h1>
            <h2>🥅 CONEXÃO SOLIDÁRIA 2025 🥅</h2>
            <div class="subtitle">Esporte, Solidariedade e Diversão em um só lugar!</div>
        </div>

        <!-- Formulário -->
        <div class="form-section">
            <h3>🎫 Compre Seu Ingresso</h3>
            
      <form method="POST" action="/processar_pagamento_pagbank">
                <div class="form-group">
                    <label>👤 Nome Completo *</label>
                    <input type="text" name="nome" required>
                </div>
                
                <div class="form-group">
                    <label>📧 E-mail *</label>
                    <input type="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label>🎂 Idade *</label>
                    <input type="number" name="idade" min="0" max="120" required>
                </div>
                
                <div class="form-group">
                    <label>🏷️ Categoria *</label>
                    <select name="categoria" required>
                        <option value="">Selecione sua categoria...</option>
                        <option value="volei_iniciante">🏐 Vôlei Iniciante + Almoço + Day Use (R$ 50,00)</option>
                        <option value="volei_intermediario">🥅 Vôlei Intermediário + Almoço + Day Use (R$ 50,00)</option>
                        <option value="almoco_day_use">🍽️ Almoço Adulto + Day Use (R$ 40,00)</option>
                     <option value="criança 6 a 12 anos_day_use">🍽️ Almoço Criança + Day Use (R$ 25,00)</option>

                    </select>
                </div>
                
                <button type="submit" class="submit-btn">🎫 Gerar Meu Ingresso</button>
            </form>
        </div>
            
            <!-- Descrição do projeto -->
            <div class="project-description">
                <h3>🌟 O que é o Conexão Solidária?</h3>
                <p>
                    O <strong>Conexão Solidária</strong>é um projeto de voluntariado nascido com amor e propósito, voltado à cidade de Manaus. Nosso objetivo é levar apoio a crianças carentes, abrigos e pessoas em situação de rua, através de ações que fazem a diferença na vida de quem mais precisa.

Acreditamos que o amor é a chave para transformar realidades — e quando nos unimos por um bem maior, cada gesto se torna luz no caminho de alguém.

🌟 Seja um voluntário. Faça parte dessa conexão que transforma vidas.
                </p>
                <br>
                <p>
                 Cada ingresso vendido contribui diretamente para fazer a diferença na 
                    vida de quem mais precisa.
                </p>
                
                <div class="project-highlights">
                    <div class="highlight-card">
                        <div class="icon">🏐</div>
                        <h4>Torneio de Vôlei</h4>
                        <p>Categorias Iniciante e Intermediário</p>
                    </div>
                    <div class="highlight-card">
                        <div class="icon">🍽️</div>
                        <h4>Almoço Completo</h4>
                        <p>Refeição para todos os participantes</p>
                    </div>
                    <div class="highlight-card">
                        <div class="icon">🏊</div>
                        <h4>Day Use</h4>
                        <p>Acesso completo às instalações</p>
                    </div>
                    <div class="highlight-card">
                        <div class="icon">❤️</div>
                        <h4>Causa Social</h4>
                        <p>100% da renda para projetos locais</p>
                    </div>
                </div>
            </div>
        </div>
            

        <!-- Links de navegação -->
        <div class="links-section">
            <a href="/editais" class="nav-btn">📋 Regulamento</a>

        </div>
    </div>
</body>
</html>
    ''')

# [Resto do código permanece igual - apenas a página inicial foi modificada]

@app.route('/gerar_ingresso', methods=['POST'])
def gerar_ingresso():
    nome = request.form['nome']
    email = request.form['email']
    idade = int(request.form['idade'])
    categoria = request.form['categoria']
    
    if idade <= 5:
        preco = 0.0
        categoria_final = "👶 Criança (0-5 anos) - GRATUITO"
    elif idade <= 12:
        preco = 20.0
        categoria_final = "🧒 Criança (6-12 anos)"
    else:
        if categoria == "volei_iniciante":
            preco = 50.0
            categoria_final = "🏐 Vôlei Iniciante + Almoço + Day Use"
        elif categoria == "volei_intermediario":
            preco = 50.0
            categoria_final = "🥅 Vôlei Intermediário + Almoço + Day Use"
        else:
            preco = 40.0
            categoria_final = "🍽️ Almoço + Day Use"
    
    ingresso_id = str(uuid.uuid4())[:8].upper()
    
    conn = sqlite3.connect('conexao_solidaria.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO ingressos (id, nome, email, telefone, idade, categoria, preco)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ingresso_id, nome, email, '', idade, categoria_final, preco))
    conn.commit()
    conn.close()
    
    # Gerar QR Code
    qr_data = f"TORNEIO:{ingresso_id}:{nome}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f'''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #9333ea;">🎫 Ingresso Gerado com Sucesso!</h2>
        <p><strong>ID:</strong> {ingresso_id}</p>
        <p><strong>Nome:</strong> {nome}</p>
        <p><strong>Categoria:</strong> {categoria_final}</p>
        <p><strong>Valor:</strong> {"GRATUITO" if preco == 0 else f"R$ {preco:.2f}"}</p>
        <img src="data:image/png;base64,{img_str}" style="margin: 20px;">
        <br>
        <a href="/" style="background: #9333ea; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">🔙 Voltar</a>
        <a href="/admin" style="background: #22c55e; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">📊 Admin</a>
    </div>
    '''

@app.route('/consultar')
def consultar():
    return '''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #9333ea;">🔍 Consultar Ingresso</h2>
        <form method="POST" action="/resultado_consulta">
            <input type="text" name="id" placeholder="ID DO INGRESSO" style="padding: 15px; font-size: 18px; margin: 20px;">
            <br>
            <button type="submit" style="background: #9333ea; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 16px;">🔍 Buscar</button>
        </form>
        <br>
        <a href="/" style="color: #C7B8EA;">🔙 Voltar</a>
    </div>
    '''

@app.route('/resultado_consulta', methods=['POST'])
def resultado_consulta():
    ingresso_id = request.form['id'].upper().strip()
    
    conn = sqlite3.connect('conexao_solidaria.db')
    c = conn.cursor()
    c.execute('SELECT * FROM ingressos WHERE id = ?', (ingresso_id,))
    ingresso = c.fetchone()
    conn.close()
    
    if not ingresso:
        return f'''
        <div style="text-align: center; margin: 50px; font-family: Arial;">
            <h2 style="color: #C7B8EA;">❌ Ingresso não encontrado!</h2>
            <a href="/consultar" style="color: #9333ea;">🔙 Tentar novamente</a>
        </div>
        '''
    
    return f'''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #9333ea;">✅ Ingresso Encontrado!</h2>
        <p><strong>ID:</strong> {ingresso[0]}</p>
        <p><strong>Nome:</strong> {ingresso[1]}</p>
        <p><strong>E-mail:</strong> {ingresso[2]}</p>
        <p><strong>Idade:</strong> {ingresso[4]} anos</p>
        <p><strong>Categoria:</strong> {ingresso[5]}</p>
        <p><strong>Valor:</strong> {"GRATUITO" if ingresso[6] == 0 else f"R$ {ingresso[6]:.2f}"}</p>
        <p><strong>Status:</strong> {"USADO" if ingresso[9] else "ATIVO"}</p>
        <br>
        <a href="/consultar" style="color: #9333ea;">🔙 Voltar</a>
    </div>
    '''

@app.route('/editais')
def editais():
    return '''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #9333ea;">📋 Regulamento do Torneio</h2>
        <p>O regulamento será publicado em breve.</p>
        <p>Acompanhe nossas redes sociais!</p>
    </div>
    '''

@app.route('/validar')
def validar():
    return '''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #22c55e;">✅ Validar Entrada</h2>
        <form method="POST" action="/processar_validacao">
            <input type="text" name="id" placeholder="ID DO INGRESSO" style="padding: 15px; font-size: 18px; margin: 20px;">
            <br>
            <button type="submit" style="background: #22c55e; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 16px;">✅ Validar</button>
        </form>
        <br>
    </div>
    '''

@app.route('/processar_validacao', methods=['POST'])
def processar_validacao():
    ingresso_id = request.form['id'].upper().strip()
    
    conn = sqlite3.connect('conexao_solidaria.db')
    c = conn.cursor()
    c.execute('SELECT * FROM ingressos WHERE id = ?', (ingresso_id,))
    ingresso = c.fetchone()
    
    if not ingresso:
        return '<div style="text-align: center; margin: 50px; font-family: Arial;"><h2 style="color: #dc2626;">❌ INGRESSO NÃO ENCONTRADO!</h2><a href="/validar">🔙 Tentar novamente</a></div>'
    
    if ingresso[9]:
        return '<div style="text-align: center; margin: 50px; font-family: Arial;"><h2 style="color: #dc2626;">🚫 INGRESSO JÁ USADO!</h2><a href="/validar">🔙 Validar outro</a></div>'
    
    # Marcar como usado
    data_uso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE ingressos SET usado = 1, data_uso = ? WHERE id = ?', (data_uso, ingresso_id))
    conn.commit()
    conn.close()
    
    return f'''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #22c55e;">✅ ENTRADA LIBERADA!</h2>
        <p><strong>Nome:</strong> {ingresso[1]}</p>
        <p><strong>Categoria:</strong> {ingresso[5]}</p>
        <p><strong>Validado em:</strong> {data_uso}</p>
        <br>
        <a href="/validar" style="background: #22c55e; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none;">✅ Validar outro</a>
    </div>
    '''
@app.route('/processar_pagamento_pagbank', methods=['POST'])
def processar_pagamento_pagbank():
    nome = request.form['nome']
    email = request.form['email']
    idade = int(request.form['idade'])
    categoria = request.form['categoria']
    
    # Lógica de preço igual à original
    if idade <= 5:
        preco = 0.0
        categoria_final = "👶 Criança (0-5 anos) - GRATUITO"
    elif categoria == "criança 6 a 12 anos_day_use":
        preco = 25.0
        categoria_final = "🧒 Criança (6-12 anos) + Day Use"
    elif categoria == "volei_iniciante":
        preco = 50.0
        categoria_final = "🏐 Vôlei Iniciante + Almoço + Day Use"
    elif categoria == "volei_intermediario":
        preco = 50.0
        categoria_final = "🥅 Vôlei Intermediário + Almoço + Day Use"
    elif categoria == "almoco_day_use":
        preco = 40.0
        categoria_final = "🍽️ Almoço Adulto + Day Use"
    else:
        preco = 25.0
        categoria_final = "🍽️ Almoço Criança + Day Use"
    
    # Se gratuito, chama a função original
    if preco == 0:
        return redirect(url_for('gerar_ingresso_original') + f'?nome={nome}&email={email}&idade={idade}&categoria_final={categoria_final}&preco={preco}')
    
    # Calcular taxas
    taxa_pix = preco * 0.0199
    taxa_cartao = preco * 0.0379 + 0.40
    valor_final_pix = preco + taxa_pix
    valor_final_cartao = preco + taxa_cartao
    
    # Mostrar opções de pagamento
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Escolha o Pagamento - Conexão Solidária</title>
        <style>
            body {{ 
                font-family: Arial; 
                background: linear-gradient(135deg, #9333ea, #e879f9, #f3e8ff);
                margin: 0; 
                padding: 20px; 
            }}
            .container {{ 
                max-width: 700px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 25px; 
                padding: 40px;
                box-shadow: 0 25px 50px rgba(147, 51, 234, 0.4);
            }}
            .payment-option {{ 
                border: 3px solid #e2e8f0; 
                border-radius: 20px; 
                padding: 30px; 
                margin: 20px 0; 
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
            }}
            .payment-option:hover {{ 
                border-color: #9333ea; 
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(147, 51, 234, 0.3);
            }}
            .payment-option.pix {{ background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }}
            .payment-option.cartao {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; }}
            .payment-icon {{ font-size: 3em; margin-bottom: 15px; }}
            .payment-title {{ font-size: 1.8em; font-weight: bold; margin-bottom: 10px; }}
            .payment-details {{ font-size: 1.1em; margin-bottom: 15px; }}
            .payment-total {{ font-size: 1.4em; font-weight: bold; margin-bottom: 20px; }}
            .btn {{ 
                background: rgba(255,255,255,0.2); 
                color: white; 
                padding: 15px 30px; 
                border: 2px solid white; 
                border-radius: 25px; 
                font-size: 1.1em; 
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
            }}
            .btn:hover {{ 
                background: white; 
                color: #333; 
            }}
            .summary {{ 
                background: #f8f9fa; 
                padding: 25px; 
                border-radius: 15px; 
                margin-bottom: 30px; 
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color: #9333ea; text-align: center; margin-bottom: 30px;">💳 Escolha sua forma de pagamento</h2>
            
            <div class="summary">
                <h3 style="color: #9333ea; margin-bottom: 15px;">📋 Resumo da Compra</h3>
                <p><strong>Nome:</strong> {nome}</p>
                <p><strong>E-mail:</strong> {email}</p>
                <p><strong>Categoria:</strong> {categoria_final}</p>
                <p><strong>Valor do Ingresso:</strong> R$ {preco:.2f}</p>
            </div>
            
            <div class="payment-option pix" onclick="window.location.href='/pagar_pix?nome={nome}&email={email}&idade={idade}&categoria_final={categoria_final}&preco={preco}'">
                <div class="payment-icon">📱</div>
                <div class="payment-title">PIX</div>
                <div class="payment-details">
                    ✅ Aprovação instantânea<br>
                    ✅ Taxa: R$ {taxa_pix:.2f} (1,99%)<br>
                    ✅ Mais econômico
                </div>
                <div class="payment-total">Total: R$ {valor_final_pix:.2f}</div>
                <div class="btn">📱 Pagar com PIX</div>
            </div>
            
            <div class="payment-option cartao" onclick="window.location.href='/pagar_cartao?nome={nome}&email={email}&idade={idade}&categoria_final={categoria_final}&preco={preco}'">
                <div class="payment-icon">💳</div>
                <div class="payment-title">Cartão de Crédito</div>
                <div class="payment-details">
                    ✅ Parcelamento disponível<br>
                    ✅ Taxa: R$ {taxa_cartao:.2f} (3,79% + R$0,40)<br>
                    ✅ Aprovação rápida
                </div>
                <div class="payment-total">Total: R$ {valor_final_cartao:.2f}</div>
                <div class="btn">💳 Pagar com Cartão</div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" style="background: #6b7280; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none;">🔙 Voltar</a>
            </div>
        </div>
    </body>
    </html>
    '''
@app.route('/pagar_pix')
def pagar_pix():
    nome = request.args.get('nome', '')
    email = request.args.get('email', '')
    idade = int(request.args.get('idade', 0))
    categoria_final = request.args.get('categoria_final', '')
    preco = float(request.args.get('preco', 0))
    
    # Gerar referência única
    reference_id = f"PIX_{uuid.uuid4().hex[:8].upper()}"
    
    # Dados para criar ordem PIX no PagBank
    order_data = {
        "reference_id": reference_id,
        "customer": {
            "name": nome,
            "email": email
        },
        "items": [
            {
                "reference_id": "item_01",
                "name": f"Ingresso - {categoria_final}",
                "quantity": 1,
                "unit_amount": int(preco * 100)
            }
        ],
        "charges": [
            {
                "reference_id": "charge_01",
                "description": f"Ingresso Conexão Solidária - {categoria_final}",
                "amount": {
                    "value": int(preco * 100),
                    "currency": "BRL"
                },
                "payment_method": {
                    "type": "PIX",
                    "pix": {
                        "expiration_date": (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S-03:00')
                    }
                }
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {PAGBANK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{PAGBANK_BASE_URL}/orders", headers=headers, json=order_data)
        
        if response.status_code == 201:
            order = response.json()
            charge = order['charges'][0]
            
            # Salvar no banco como pendente
            conn = sqlite3.connect('conexao_solidaria.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO ingressos (id, nome, email, telefone, idade, categoria, preco, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (reference_id, nome, email, '', idade, categoria_final, preco, 'pendente_pix'))
            conn.commit()
            conn.close()
            
            pix_qr_code = charge['payment_method']['pix']['qr_code']
            pix_text = charge['payment_method']['pix']['qr_code_base64']
            
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Pagamento PIX - Conexão Solidária</title>
                <style>
                    body {{ font-family: Arial; text-align: center; margin: 20px; background: #f8f9fa; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 25px; }}
                    .qr-code {{ margin: 30px 0; }}
                    .pix-code {{ 
                        background: #f8f9fa; padding: 15px; border-radius: 10px; 
                        font-family: monospace; word-break: break-all; font-size: 12px;
                        margin: 20px 0; border: 2px dashed #22c55e;
                    }}
                    .btn {{ 
                        background: #22c55e; color: white; padding: 15px 30px; 
                        border: none; border-radius: 25px; margin: 10px; cursor: pointer;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2 style="color: #22c55e;">📱 Pagamento via PIX</h2>
                    <p><strong>Nome:</strong> {nome}</p>
                    <p><strong>Valor:</strong> R$ {preco:.2f}</p>
                    <p><strong>ID:</strong> {reference_id}</p>
                    
                    <div class="qr-code">
                        <h3>📱 Escaneie o QR Code:</h3>
                        <img src="data:image/png;base64,{pix_text}" style="max-width: 300px;">
                    </div>
                    
                    <div>
                        <h4>📋 Ou copie o código PIX:</h4>
                        <div class="pix-code" id="pixCode">{pix_qr_code}</div>
                        <button class="btn" onclick="copyPix()">📋 Copiar Código PIX</button>
                    </div>
                    
                    <div style="background: #d1fae5; padding: 20px; border-radius: 10px; margin: 30px 0;">
                        <h4>⚡ Pagamento será confirmado automaticamente!</h4>
                        <p>Após o PIX, seu ingresso será gerado na hora!</p>
                    </div>
                    
                    <a href="/" style="background: #9333ea; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none;">🔙 Voltar</a>
                </div>
                
                <script>
                function copyPix() {{
                    const pixCode = document.getElementById('pixCode').innerText;
                    navigator.clipboard.writeText(pixCode).then(() => {{
                        alert('Código PIX copiado!');
                    }});
                }}
                </script>
            </body>
            </html>
            '''
        else:
            return f'<div style="text-align: center;"><h2>❌ Erro ao gerar PIX</h2><p>{response.text}</p></div>'
    except Exception as e:
        return f'<div style="text-align: center;"><h2>❌ Erro</h2><p>{str(e)}</p></div>'

@app.route('/pagar_cartao')
def pagar_cartao():
    nome = request.args.get('nome', '')
    email = request.args.get('email', '')
    preco = float(request.args.get('preco', 0))
    categoria_final = request.args.get('categoria_final', '')
    
    return f'''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #3b82f6;">💳 Pagamento com Cartão</h2>
        <p><strong>Nome:</strong> {nome}</p>
        <p><strong>Valor:</strong> R$ {preco:.2f}</p>
        
        <div style="background: #fff3cd; padding: 30px; border-radius: 15px; margin: 30px 0;">
            <h3>🚧 Em desenvolvimento</h3>
            <p>A integração com cartão estará disponível em breve!</p>
            <p>Por enquanto, use o PIX que é mais barato! 😉</p>
        </div>
        
        <a href="/processar_pagamento_pagbank" style="background: #22c55e; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">📱 Usar PIX</a>
        <a href="/" style="background: #9333ea; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">🔙 Voltar</a>
    </div>
    '''
    nome = request.form['nome']
    email = request.form['email']
    idade = int(request.form['idade'])
    categoria = request.form['categoria']
    
    # Lógica de preço igual à original
    if idade <= 5:
        preco = 0.0
        categoria_final = "👶 Criança (0-5 anos) - GRATUITO"
    elif categoria == "criança 6 a 12 anos_day_use":
        preco = 25.0
        categoria_final = "🧒 Criança (6-12 anos) + Day Use"
    elif categoria == "volei_iniciante":
        preco = 50.0
        categoria_final = "🏐 Vôlei Iniciante + Almoço + Day Use"
    elif categoria == "volei_intermediario":
        preco = 50.0
        categoria_final = "🥅 Vôlei Intermediário + Almoço + Day Use"
    elif categoria == "almoco_day_use":
        preco = 40.0
        categoria_final = "🍽️ Almoço Adulto + Day Use"
    else:
        preco = 25.0
        categoria_final = "🍽️ Almoço Criança + Day Use"
    
    # Se gratuito, chama a função original
    if preco == 0:
        return redirect(url_for('gerar_ingresso_original') + f'?nome={nome}&email={email}&idade={idade}&categoria_final={categoria_final}&preco={preco}')
    
    # Para pagos, mostrar opção de pagamento
    return f'''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #9333ea;">💳 Finalizar Pagamento - PagBank</h2>
        <p><strong>Nome:</strong> {nome}</p>
        <p><strong>Categoria:</strong> {categoria_final}</p>
        <p><strong>Valor:</strong> R$ {preco:.2f}</p>
        <p><strong>Taxa PagBank:</strong> R$ {preco * 0.0199:.2f} (1,99%)</p>
        
        <div style="margin: 30px 0;">
            <p style="background: #fff3cd; padding: 20px; border-radius: 10px;">
                🚧 <strong>Integração em desenvolvimento...</strong><br>
                Por enquanto, use a opção original abaixo:
            </p>
        </div>
        
        <a href="/gerar_ingresso_original?nome={nome}&email={email}&idade={idade}&categoria_final={categoria_final}&preco={preco}" 
           style="background: #22c55e; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">
           🎫 Gerar Ingresso (Temporário)
        </a>
        <br><br>
        <a href="/" style="background: #9333ea; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none;">🔙 Voltar</a>
    </div>
    '''

@app.route('/gerar_ingresso_original')
def gerar_ingresso_original():
    nome = request.args.get('nome', '')
    email = request.args.get('email', '')
    idade = int(request.args.get('idade', 0))
    categoria_final = request.args.get('categoria_final', '')
    preco = float(request.args.get('preco', 0))
    
    ingresso_id = str(uuid.uuid4())[:8].upper()
    
    conn = sqlite3.connect('conexao_solidaria.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO ingressos (id, nome, email, telefone, idade, categoria, preco)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ingresso_id, nome, email, '', idade, categoria_final, preco))
    conn.commit()
    conn.close()
    
    # Gerar QR Code
    qr_data = f"TORNEIO:{ingresso_id}:{nome}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f'''
    <div style="text-align: center; margin: 50px; font-family: Arial;">
        <h2 style="color: #9333ea;">🎫 Ingresso Gerado com Sucesso!</h2>
        <p><strong>ID:</strong> {ingresso_id}</p>
        <p><strong>Nome:</strong> {nome}</p>
        <p><strong>Categoria:</strong> {categoria_final}</p>
        <p><strong>Valor:</strong> {"GRATUITO" if preco == 0 else f"R$ {preco:.2f}"}</p>
        <img src="data:image/png;base64,{img_str}" style="margin: 20px;">
        <br>
        <a href="/" style="background: #9333ea; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">🔙 Voltar</a>
        <a href="/admin" style="background: #22c55e; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">📊 Admin</a>
    </div>
    '''
@app.route('/admin')
def admin():
    conn = sqlite3.connect('conexao_solidaria.db')
    c = conn.cursor()
    c.execute('SELECT * FROM ingressos ORDER BY data_compra DESC')
    ingressos = c.fetchall()
    
    c.execute('SELECT COUNT(*) FROM ingressos')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM ingressos WHERE usado = 1')
    usados = c.fetchone()[0]
    
    c.execute('SELECT SUM(preco) FROM ingressos')
    receita = c.fetchone()[0] or 0
    
    conn.close()
    
    html = f'''
    <div style="margin: 20px; font-family: Arial;">
        <h1 style="color: #9333ea; text-align: center;">📊 Painel Administrativo</h1>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="background: white; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #3b82f6;">
                <h2 style="color: #3b82f6; margin: 0;">{total}</h2>
                <p>🎫 Total de Ingressos</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #22c55e;">
                <h2 style="color: #22c55e; margin: 0;">{usados}</h2>
                <p>✅ Validados</p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #f59e0b;">
                <h2 style="color: #f59e0b; margin: 0;">R$ {receita:.2f}</h2>
                <p>💰 Receita Total</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="/validar" style="background: #22c55e; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">✅ Validar Entrada</a>
            <a href="/" style="background: #9333ea; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 10px;">🏠 Página Inicial</a>
        </div>
        
        <h3 style="color: #9333ea;">📋 Lista de Ingressos</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr style="background: #f8f9fa;">
                <th style="padding: 10px; border: 1px solid #ddd;">ID</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Nome</th>
                <th style="padding: 10px; border: 1px solid #ddd;">E-mail</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Categoria</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Valor</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
            </tr>
    '''
    
    for ingresso in ingressos:
        status = "USADO" if ingresso[9] else "ATIVO"
        status_color = "#22c55e" if ingresso[9] else "#3b82f6"
        html += f'''
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>{ingresso[0]}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ingresso[1]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ingresso[2]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ingresso[5]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{"GRATUITO" if ingresso[6] == 0 else f"R$ {ingresso[6]:.2f}"}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">{status}</td>
            </tr>
        '''
    
    html += '</table></div>'
    return html

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=8080)