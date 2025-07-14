"""
Sistema de Relatórios e Analytics
"""

from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime, timedelta
import json
import sqlite3
import os
import io
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

reports_bp = Blueprint('reports', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database.db')

def init_reports_db():
    """Inicializar tabelas de relatórios"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            frequency TEXT NOT NULL,
            email_recipients TEXT,
            last_sent TIMESTAMP,
            next_send TIMESTAMP,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            date_range TEXT NOT NULL,
            data TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@reports_bp.route('/generate', methods=['GET'])
def generate_report():
    """Gerar relatório específico"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        report_type = request.args.get('type', 'cost')
        date_range = request.args.get('range', '30d')
        
        # Verificar cache primeiro
        cached_data = get_cached_report(session['user_id'], report_type, date_range)
        if cached_data:
            return jsonify(cached_data), 200
        
        # Gerar novo relatório
        if report_type == 'cost':
            data = generate_cost_optimization_report(date_range)
        elif report_type == 'resources':
            data = generate_resource_utilization_report(date_range)
        elif report_type == 'security':
            data = generate_security_compliance_report(date_range)
        elif report_type == 'performance':
            data = generate_performance_report(date_range)
        else:
            return jsonify({'error': 'Tipo de relatório inválido'}), 400
        
        # Salvar no cache
        cache_report(session['user_id'], report_type, date_range, data)
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_cost_optimization_report(date_range):
    """Gerar relatório de otimização de custos"""
    # Simular dados reais (em produção, viria do Azure Cost Management)
    import random
    
    # Custos por serviço
    services = ['Virtual Machines', 'Storage', 'App Service', 'SQL Database', 'Networking', 'Others']
    costs_by_service = []
    total_cost = 0
    
    for service in services:
        cost = random.uniform(50, 500)
        total_cost += cost
        costs_by_service.append({
            'service': service,
            'cost': round(cost, 2)
        })
    
    # Recomendações de economia
    recommendations = [
        {
            'title': 'Redimensionar VMs Subutilizadas',
            'description': 'Identificamos 3 VMs com utilização de CPU abaixo de 20%. Redimensionar pode economizar até 40%.',
            'savings': 180.50
        },
        {
            'title': 'Remover Discos Órfãos',
            'description': '5 discos não anexados encontrados. Removê-los eliminará custos desnecessários.',
            'savings': 95.30
        },
        {
            'title': 'Otimizar Storage Tier',
            'description': 'Mover dados antigos para tier Cool pode reduzir custos de storage em 60%.',
            'savings': 120.75
        },
        {
            'title': 'Reserved Instances',
            'description': 'Comprar instâncias reservadas para VMs de produção pode economizar até 72%.',
            'savings': 450.00
        }
    ]
    
    potential_savings = sum(rec['savings'] for rec in recommendations)
    
    return {
        'currentSpend': total_cost,
        'potentialSavings': potential_savings,
        'efficiency': round((total_cost - potential_savings) / total_cost * 100, 1),
        'costsByService': costs_by_service,
        'recommendations': recommendations
    }

def generate_resource_utilization_report(date_range):
    """Gerar relatório de utilização de recursos"""
    import random
    
    # Distribuição de recursos
    resource_distribution = [
        {'name': 'Virtual Machines', 'value': 25},
        {'name': 'Storage Accounts', 'value': 15},
        {'name': 'App Services', 'value': 12},
        {'name': 'Databases', 'value': 8},
        {'name': 'Networking', 'value': 10},
        {'name': 'Others', 'value': 30}
    ]
    
    return {
        'underutilizedVMs': random.randint(3, 8),
        'orphanedStorage': random.randint(2, 6),
        'unusedIPs': random.randint(1, 4),
        'overallEfficiency': random.randint(75, 90),
        'resourceDistribution': resource_distribution
    }

def generate_security_compliance_report(date_range):
    """Gerar relatório de conformidade de segurança"""
    import random
    
    security_checks = [
        {
            'name': 'Criptografia em Trânsito',
            'description': 'Verificar se todos os serviços usam HTTPS/TLS',
            'status': 'pass'
        },
        {
            'name': 'Controle de Acesso',
            'description': 'Validar configurações de RBAC e IAM',
            'status': 'pass'
        },
        {
            'name': 'Backup e Recuperação',
            'description': 'Verificar políticas de backup automático',
            'status': 'warning'
        },
        {
            'name': 'Monitoramento de Logs',
            'description': 'Auditoria e logs de segurança habilitados',
            'status': 'pass'
        },
        {
            'name': 'Atualizações de Segurança',
            'description': 'VMs com patches de segurança atualizados',
            'status': 'fail'
        }
    ]
    
    return {
        'securityScore': random.randint(80, 95),
        'vulnerabilities': random.randint(1, 5),
        'complianceScore': random.randint(85, 98),
        'securityChecks': security_checks
    }

def generate_performance_report(date_range):
    """Gerar relatório de performance"""
    import random
    from datetime import datetime, timedelta
    
    # Histórico de performance
    performance_history = []
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        performance_history.append({
            'timestamp': date.strftime('%Y-%m-%d'),
            'latency': random.uniform(30, 80),
            'throughput': random.randint(1000, 1500)
        })
    
    return {
        'availability': round(random.uniform(99.5, 99.99), 2),
        'avgLatency': random.randint(35, 60),
        'throughput': random.randint(1200, 1400),
        'errorRate': round(random.uniform(0.01, 0.5), 2),
        'performanceHistory': performance_history
    }

@reports_bp.route('/export', methods=['POST'])
def export_report():
    """Exportar relatório em formato específico"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        report_type = data.get('type')
        date_range = data.get('range')
        export_format = data.get('format', 'pdf')
        
        # Obter dados do relatório
        if report_type == 'cost':
            report_data = generate_cost_optimization_report(date_range)
        elif report_type == 'resources':
            report_data = generate_resource_utilization_report(date_range)
        elif report_type == 'security':
            report_data = generate_security_compliance_report(date_range)
        elif report_type == 'performance':
            report_data = generate_performance_report(date_range)
        else:
            return jsonify({'error': 'Tipo de relatório inválido'}), 400
        
        if export_format == 'pdf':
            return export_pdf_report(report_type, report_data, date_range)
        elif export_format == 'excel':
            return export_excel_report(report_type, report_data, date_range)
        elif export_format == 'csv':
            return export_csv_report(report_type, report_data, date_range)
        else:
            return jsonify({'error': 'Formato de exportação inválido'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def export_pdf_report(report_type, data, date_range):
    """Exportar relatório em PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    report_titles = {
        'cost': 'Relatório de Otimização de Custos',
        'resources': 'Relatório de Utilização de Recursos',
        'security': 'Relatório de Conformidade de Segurança',
        'performance': 'Relatório de Performance'
    }
    
    story.append(Paragraph(report_titles.get(report_type, 'Relatório'), title_style))
    story.append(Spacer(1, 12))
    
    # Data de geração
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"Período: {date_range}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Conteúdo específico por tipo
    if report_type == 'cost':
        story.append(Paragraph("Resumo Executivo", styles['Heading2']))
        story.append(Paragraph(f"Gasto Atual: R$ {data['currentSpend']:.2f}", styles['Normal']))
        story.append(Paragraph(f"Economia Potencial: R$ {data['potentialSavings']:.2f}", styles['Normal']))
        story.append(Paragraph(f"Eficiência: {data['efficiency']}%", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tabela de custos por serviço
        story.append(Paragraph("Custos por Serviço", styles['Heading2']))
        table_data = [['Serviço', 'Custo (R$)']]
        for item in data['costsByService']:
            table_data.append([item['service'], f"R$ {item['cost']:.2f}"])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'relatorio-{report_type}-{date_range}.pdf',
        mimetype='application/pdf'
    )

def export_excel_report(report_type, data, date_range):
    """Exportar relatório em Excel"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if report_type == 'cost':
            # Aba de custos por serviço
            df_costs = pd.DataFrame(data['costsByService'])
            df_costs.to_excel(writer, sheet_name='Custos por Serviço', index=False)
            
            # Aba de recomendações
            df_recommendations = pd.DataFrame(data['recommendations'])
            df_recommendations.to_excel(writer, sheet_name='Recomendações', index=False)
        
        elif report_type == 'resources':
            df_resources = pd.DataFrame(data['resourceDistribution'])
            df_resources.to_excel(writer, sheet_name='Distribuição de Recursos', index=False)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'relatorio-{report_type}-{date_range}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_csv_report(report_type, data, date_range):
    """Exportar relatório em CSV"""
    buffer = io.StringIO()
    
    if report_type == 'cost':
        df = pd.DataFrame(data['costsByService'])
        df.to_csv(buffer, index=False)
    elif report_type == 'resources':
        df = pd.DataFrame(data['resourceDistribution'])
        df.to_csv(buffer, index=False)
    
    output = buffer.getvalue()
    buffer.close()
    
    return send_file(
        io.BytesIO(output.encode()),
        as_attachment=True,
        download_name=f'relatorio-{report_type}-{date_range}.csv',
        mimetype='text/csv'
    )

@reports_bp.route('/schedule', methods=['POST'])
def schedule_report():
    """Agendar relatório automático"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calcular próximo envio
        from datetime import datetime, timedelta
        next_send = datetime.now() + timedelta(days=7)  # Semanal por padrão
        
        cursor.execute('''
            INSERT INTO scheduled_reports (user_id, report_type, frequency, email_recipients, next_send)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['type'],
            data.get('frequency', 'weekly'),
            json.dumps([session.get('user_email', 'user@example.com')]),
            next_send.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Relatório agendado com sucesso'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_cached_report(user_id, report_type, date_range):
    """Obter relatório do cache se válido"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data FROM report_cache 
            WHERE user_id = ? AND report_type = ? AND date_range = ? 
            AND expires_at > CURRENT_TIMESTAMP
        ''', (user_id, report_type, date_range))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
        
    except Exception:
        return None

def cache_report(user_id, report_type, date_range, data):
    """Salvar relatório no cache"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Cache válido por 1 hora
        expires_at = datetime.now() + timedelta(hours=1)
        
        cursor.execute('''
            INSERT OR REPLACE INTO report_cache 
            (user_id, report_type, date_range, data, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, report_type, date_range, json.dumps(data), expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao salvar cache: {e}")

# Inicializar banco ao importar
init_reports_db()

