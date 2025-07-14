// Script para corrigir problemas do frontend do BOLT Dashboard

// Função para atualizar contadores automaticamente
async function updateCounters() {
    try {
        console.log('Atualizando contadores...');
        
        // Buscar dados das APIs
        const [rgResponse, locksResponse] = await Promise.all([
            fetch('/api/azure-test/list-resource-groups').then(r => r.json()),
            fetch('/api/azure-actions/list-locks').then(r => r.json())
        ]);
        
        console.log('RG Response:', rgResponse);
        console.log('Locks Response:', locksResponse);
        
        // Encontrar os elementos dos contadores
        const statusValues = document.querySelectorAll('.status-value');
        
        if (statusValues.length >= 2) {
            // Atualizar Resource Groups counter
            if (rgResponse.resource_groups) {
                statusValues[0].textContent = rgResponse.resource_groups.length;
                console.log('Updated RG counter to:', rgResponse.resource_groups.length);
            } else if (rgResponse.error) {
                statusValues[0].textContent = '0';
                console.log('RG API error:', rgResponse.error);
            }
            
            // Atualizar Locks counter  
            if (locksResponse.locks) {
                statusValues[1].textContent = locksResponse.locks.length;
                console.log('Updated Locks counter to:', locksResponse.locks.length);
            } else if (locksResponse.error) {
                statusValues[1].textContent = '0';
                console.log('Locks API error:', locksResponse.error);
            }
        }
        
        return {
            resourceGroups: rgResponse.resource_groups?.length || 0,
            locks: locksResponse.locks?.length || 0
        };
    } catch (error) {
        console.error('Error updating counters:', error);
        return { resourceGroups: 0, locks: 0 };
    }
}

// Função para corrigir o formulário de Lock
function fixLockForm() {
    console.log('Corrigindo formulário de Lock...');
    
    // Encontrar o botão de criar lock
    const createLockButton = document.querySelector('button:contains("🔒 Criar Lock")') || 
                            Array.from(document.querySelectorAll('button')).find(btn => 
                                btn.textContent.includes('Criar Lock'));
    
    if (createLockButton) {
        console.log('Botão Criar Lock encontrado');
        
        // Remover event listeners antigos
        createLockButton.replaceWith(createLockButton.cloneNode(true));
        const newButton = document.querySelector('button:contains("🔒 Criar Lock")') || 
                         Array.from(document.querySelectorAll('button')).find(btn => 
                             btn.textContent.includes('Criar Lock'));
        
        // Adicionar novo event listener
        newButton.addEventListener('click', async function(e) {
            e.preventDefault();
            console.log('Botão Criar Lock clicado');
            
            try {
                // Capturar dados do formulário
                const nameInput = document.querySelector('input[placeholder*="lock"]');
                const scopeSelect = document.querySelector('select option[selected]') || 
                                  document.querySelector('select').options[document.querySelector('select').selectedIndex];
                const levelSelect = document.querySelectorAll('select')[1];
                const levelOption = levelSelect.options[levelSelect.selectedIndex];
                const notesTextarea = document.querySelector('textarea');
                
                const lockData = {
                    name: nameInput ? nameInput.value.trim() : '',
                    scope: scopeSelect ? (scopeSelect.textContent.includes('Subscription') ? 'subscription' : 'resource-group') : 'subscription',
                    level: levelOption ? (levelOption.textContent.includes('CanNotDelete') ? 'CanNotDelete' : 'ReadOnly') : 'CanNotDelete',
                    notes: notesTextarea ? notesTextarea.value.trim() : 'Lock criado pelo BOLT Dashboard'
                };
                
                console.log('Dados do Lock:', lockData);
                
                // Validar dados
                if (!lockData.name) {
                    alert('❌ Nome do lock é obrigatório');
                    return;
                }
                
                if (!lockData.level) {
                    alert('❌ Nível do lock é obrigatório');
                    return;
                }
                
                // Enviar requisição
                console.log('Enviando requisição para criar lock...');
                const response = await fetch('/api/azure-actions/create-lock', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(lockData)
                });
                
                const result = await response.json();
                console.log('Resultado da criação do lock:', result);
                
                if (result.success) {
                    alert('✅ ' + result.message);
                    // Atualizar contadores
                    updateCounters();
                    // Limpar formulário
                    if (nameInput) nameInput.value = '';
                    if (notesTextarea) notesTextarea.value = 'Lock criado pelo BOLT Dashboard para controle de gastos';
                } else {
                    alert('❌ ' + (result.error || 'Erro ao criar lock'));
                }
                
            } catch (error) {
                console.error('Erro ao criar lock:', error);
                alert('❌ Erro ao criar lock: ' + error.message);
            }
        });
        
        console.log('Event listener do Lock adicionado');
    } else {
        console.log('Botão Criar Lock não encontrado');
    }
}

// Função para inicializar correções
function initializeFixes() {
    console.log('Inicializando correções do frontend...');
    
    // Aguardar DOM estar pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                updateCounters();
                fixLockForm();
            }, 1000);
        });
    } else {
        setTimeout(() => {
            updateCounters();
            fixLockForm();
        }, 1000);
    }
    
    // Atualizar contadores periodicamente
    setInterval(updateCounters, 30000); // A cada 30 segundos
}

// Inicializar quando script carregar
initializeFixes();

console.log('Script de correção do frontend carregado!');

