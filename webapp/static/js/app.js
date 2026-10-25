// Inicializar Telegram WebApp API
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
    tg.expand();
    tg.ready();
}

function adjustValue(inputId, delta) {
    const input = document.getElementById(inputId);
    if (!input) return;
    let val = parseInt(input.value) || 0;
    val = Math.max(0, val + delta);
    input.value = val;
}

document.getElementById('production-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerText = 'Calculando insumos...';

    const payload = {
        cachitos: parseInt(document.getElementById('cachitos')?.value) || 0,
        panes_piñitas: parseInt(document.getElementById('panes_piñitas')?.value) || 0,
        panes_de_queso: parseInt(document.getElementById('panes_de_queso')?.value) || 0,
        tequeños_grandes: parseInt(document.getElementById('tequeños_grandes')?.value) || 0,
        pastelitos_grandes: parseInt(document.getElementById('pastelitos_grandes')?.value) || 0,
        pasapalos: parseInt(document.getElementById('pasapalos')?.value) || 0,
        pizza_familiar: parseInt(document.getElementById('pizza_familiar')?.value) || 0,
        pizza_personal: parseInt(document.getElementById('pizza_personal')?.value) || 0,
        baguette: parseInt(document.getElementById('baguette')?.value) || 0
    };

    try {
        const response = await fetch('/api/production', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        if (data.status === 'ok') {
            document.getElementById('result-summary').innerHTML = data.summary.replace(/\n/g, '<br>');
            document.getElementById('result-modal').classList.remove('hidden');
        } else {
            alert('Error guardando producción');
        }
    } catch (err) {
        console.error(err);
        alert('Error conectando con el servidor');
    } finally {
        btn.disabled = false;
        btn.innerText = '💾 Guardar y Calcular Lista de Compras';
    }
});

function closeModal() {
    document.getElementById('result-modal').classList.add('hidden');
}

function confirmAndClose() {
    if (tg) {
        tg.close();
    } else {
        closeModal();
        alert('¡Producción confirmada exitosamente!');
    }
}
