// -*- coding: utf-8 -*-
// Inicialização do sistema de chat
// Este arquivo garante que todas as dependências estejam carregadas e funcionando

console.log('Iniciando sistema de chat...');

// Verificar se as dependências básicas estão disponíveis
function checkDependencies() {
    const dependencies = [
        { name: 'showToast', func: window.showToast },
        { name: 'showLoadingToast', func: window.showLoadingToast },
        { name: 'finishLoadingToast', func: window.finishLoadingToast },
        { name: 'updateLoadingToast', func: window.updateLoadingToast },
        { name: 'escapeHtml', func: window.escapeHtml },
    ];

    const missing = [];
    dependencies.forEach(dep => {
        if (typeof dep.func !== 'function') {
            missing.push(dep.name);
            console.error(`Dependência ausente: ${dep.name}`);
        }
    });

    if (missing.length > 0) {
        console.error('Dependências ausentes:', missing);
        // Fallback functions
        if (!window.showToast) {
            window.showToast = function(message, type = 'info') {
                console.log(`[TOAST ${type.toUpperCase()}] ${message}`);
                alert(`${type.toUpperCase()}: ${message}`);
            };
        }
        if (!window.escapeHtml) {
            window.escapeHtml = function(text) {
                if (!text) return '';
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };
        }
        return false;
    }
    
    console.log('Todas as dependências estão disponíveis');
    return true;
}

// Aguardar o DOM estar completamente carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, verificando dependências...');
    
    // Pequeno delay para garantir que os scripts tenham carregado
    setTimeout(() => {
        const dependenciesOK = checkDependencies();
        
        if (dependenciesOK) {
            console.log('Dependências OK, inicializando chat...');
            initializeChat();
        } else {
            console.error('Falha ao carregar dependências');
            showToast('Erro ao carregar o sistema de chat', 'error');
        }
    }, 100);
});

function initializeChat() {
    console.log('Inicializando funcionalidades do chat...');
    
    // Verificar se os elementos necessários existem
    const requiredElements = [
        'message-form',
        'message-input',
        'send-button',
        'ai-toggle',
        'messages-container'
    ];
    
    const missingElements = [];
    requiredElements.forEach(id => {
        if (!document.getElementById(id)) {
            missingElements.push(id);
        }
    });
    
    if (missingElements.length > 0) {
        console.error('Elementos HTML ausentes:', missingElements);
        return;
    }
    
    console.log('Todos os elementos HTML necessários estão presentes');
    
    // Inicializar estados globais
    if (typeof window.currentPhoneNumber === 'undefined') {
        window.currentPhoneNumber = null;
    }
    if (typeof window.currentPhoneId === 'undefined') {
        window.currentPhoneId = null;
    }
    if (typeof window.currentAIStatus === 'undefined') {
        window.currentAIStatus = false;
    }
    
    // Mostrar toast de inicialização bem-sucedida
    showToast('Sistema de chat inicializado', 'success');
    
    console.log('Chat inicializado com sucesso!');
}
