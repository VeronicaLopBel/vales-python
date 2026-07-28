import { useState } from 'react';
import './App.css';

const services = [
  { id: 'trucknet', label: 'Truck net' },
  { id: 'xiga', label: 'XIGA' },
  { id: 'xiga-prog', label: 'XIGA PROG' },
];

function App() {
  const [status, setStatus] = useState({
    trucknet: 'Esperando...',
    xiga: 'Esperando...',
    'xiga-prog': 'Esperando...',
  });
  const [busy, setBusy] = useState(false);

  const callService = async (serviceId) => {
    setBusy(true);
    setStatus((prev) => ({ ...prev, [serviceId]: 'Llamando...' }));

    const url = `http://127.0.0.1:8000/api/${serviceId}`;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const contentType = resp.headers.get('content-type') || '';
      let data;
      if (contentType.includes('application/json')) {
        data = await resp.json();
      } else {
        const text = await resp.text();
        throw new Error(`Respuesta inesperada del backend: ${text || resp.statusText}`);
      }
      if (!resp.ok) throw new Error(data?.message || 'Error inesperado');
      setStatus((prev) => ({
        ...prev,
        [serviceId]: `OK: ${data.descargados ?? 'OK'}`,
      }));
    } catch (error) {
      setStatus((prev) => ({
        ...prev,
        [serviceId]: `Error: ${error.message}`,
      }));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="panel">
        <div className="range">
          <div>Desde: 01-23-26</div>
          <div>A: 01-30-26</div>
        </div>

        {services.map((service) => (
          <div key={service.id} className="service-card">
            <button
              className="service-button"
              onClick={() => callService(service.id)}
              disabled={busy}
            >
              {service.label}
            </button>
            <div className="status-row">Descargados: {status[service.id]}</div>
          </div>
        ))}
      </div>
      <div className="footer">
        <div className="status-block">
          <div>TruckNet</div>
          <div>{status.trucknet}</div>
        </div>
        <div className="status-block">
          <div>XIGA</div>
          <div>{status.xiga}</div>
        </div>
        <div className="status-block">
          <div>XIGA PROG</div>
          <div>{status['xiga-prog']}</div>
        </div>
      </div>
    </div>
  );
}

export default App;
