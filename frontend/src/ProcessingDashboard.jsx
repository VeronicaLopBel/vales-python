import { useState, useEffect, useRef } from 'react';
import { Container, Grid, Card, CardContent, Divider } from '@mui/material';
import HeaderPanel from './HeaderPanel';
import ServiceCard from './ServiceCard';

const services = [
  { id: 'trucknet', name: 'Truck net' },
  { id: 'xiga', name: 'XIGA' },
  { id: 'xiga-prog', name: 'XIGA PROG' },
];

const formatDate = (date) => date.toISOString().slice(0, 10);

const mapEstado = (data) => ({
  descargados: data.descargados ?? 0,
  no_validos: data.no_validos ?? 0,
  repetidos: data.repetidos ?? 0,
  anadidos: data.anadidos ?? 0,
  origen: data.origen ?? 'automatico',
});


function ProcessingDashboard() {
  // Valores default: hoy y hoy-15, solo se usan para inicializar el estado
  const today = new Date();
  const fromDateDefault = new Date(today);
  fromDateDefault.setDate(today.getDate() - 15);

  // Estado editable de fechas (lo que realmente se manda al backend)
  const [fromDate, setFromDate] = useState(formatDate(fromDateDefault));
  const [toDate, setToDate] = useState(formatDate(today));

  const [serviceStatus, setServiceStatus] = useState({
    trucknet: 'Esperando inicio de proceso...',
    xiga: 'Esperando inicio de proceso...',
    'xiga-prog': 'Esperando inicio de proceso...',
  });
  const [serviceResults, setServiceResults] = useState({
    trucknet: null,
    xiga: null,
    'xiga-prog': null,
  });
  const [busy, setBusy] = useState(false);


  const ultimaVistaRef = useRef({ trucknet: null, xiga: null, 'xiga-prog': null });

   useEffect(() => {
    const consultarStatus = async () => {
      try {
        const resp = await fetch('/api/status');
        if (!resp.ok) return;
        const data = await resp.json();
        const estado = data?.estado;
        if (!estado) return;

        Object.keys(estado).forEach((serviceId) => {
          const resultado = estado[serviceId];
          if (!resultado) return;

          // evita re-renderizar si ya mostramos exactamente este mismo resultado
          const marca = JSON.stringify(resultado);
          if (ultimaVistaRef.current[serviceId] === marca) return;
          ultimaVistaRef.current[serviceId] = marca;

          setServiceResults((prev) => ({
            ...prev,
            [serviceId]: mapEstado(resultado),
          }));
          setServiceStatus((prev) => ({
            ...prev,
            [serviceId]: 'Proceso completado (automático)',
          }));
        });
      } catch (err) {
        // silencioso: si /api/status falla, no interrumpe el resto del front
        console.error('Error consultando /api/status', err);
      }
    };

    consultarStatus(); // primera consulta al cargar la página
    const intervalId = setInterval(consultarStatus, 15000); // cada 15s

    return () => clearInterval(intervalId); // limpieza al desmontar
  }, []);


  const resetFechas = () => {
    const hoy = new Date();
    const desde = new Date(hoy);
    desde.setDate(hoy.getDate() - 15);
    setFromDate(formatDate(desde));
    setToDate(formatDate(hoy));
  };

  const callService = async (serviceId) => {
    setBusy(true);
    setServiceStatus((prev) => ({
      ...prev,
      [serviceId]: 'Llamando...',
    }));
    setServiceResults((prev) => ({
      ...prev,
      [serviceId]: null,
    }));

    try {
      const resp = await fetch(`/api/${serviceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fromDate, toDate }), // <-- usa el estado, no fechas recalculadas
      });

      const contentType = resp.headers.get('content-type') || '';
      let data;
      if (contentType.includes('application/json')) {
        data = await resp.json();
      } else {
        const text = await resp.text();
        throw new Error(`Respuesta inesperada del backend: ${text || resp.statusText}`);
      }

      if (!resp.ok) {
        throw new Error(data?.message || 'Error inesperado');
      }

      let results = null;
      if (
        data?.descargados != null ||
        data?.no_validos != null ||
        data?.repetidos != null ||
        data?.anadidos != null
      ) {
        results = {
          descargados: data.descargados ?? 0,
          no_validos: data.no_validos ?? 0,
          repetidos: data.repetidos ?? 0,
          anadidos: data.anadidos ?? 0,
          origen: data.origen ?? 'manual',
        };
      }

      if (serviceId === 'xiga' && data?.xiga1 && data?.xiga2) {
        setServiceResults((prev) => ({
          ...prev,
          xiga: {
            descargados: data.xiga1.descargados ?? 0,
            no_validos: data.xiga1.no_validos ?? 0,
            repetidos: data.xiga1.repetidos ?? 0,
            anadidos: data.xiga1.anadidos ?? 0,
            origen: data.xiga1.origen ?? 'manual',
          },
        }));
        setServiceStatus((prev) => ({
          ...prev,
          xiga: 'Resultado cuenta 1 y cuenta 2 recibidos.',
        }));
      } else {
        if (results) {
          setServiceResults((prev) => ({
            ...prev,
            [serviceId]: results,
          }));
          setServiceStatus((prev) => ({
            ...prev,
            [serviceId]: 'Proceso completado',
          }));
        } else {
          setServiceStatus((prev) => ({
            ...prev,
            [serviceId]: `Resultado: ${JSON.stringify(data)}`,
          }));
        }
      }
    } catch (error) {
      setServiceStatus((prev) => ({
        ...prev,
        [serviceId]: `Error: ${error.message}`,
      }));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Card raised sx={{ borderRadius: 3, bgcolor: '#fbfbfb' }}>
        <HeaderPanel
          fromDate={fromDate}
          toDate={toDate}
          onChangeFromDate={setFromDate}
          onChangeToDate={setToDate}
          onReset={resetFechas}
          disabled={busy}
        />
        <Divider />
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={3} justifyContent="space-between">
            {services.map((service) => (
              <Grid item xs={12} md={4} key={service.id}>
                <ServiceCard
                  name={service.name}
                  results={serviceResults[service.id]}
                  status={serviceStatus[service.id]}
                  onProcess={() => callService(service.id)}
                  disabled={busy}
                />
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
}

export default ProcessingDashboard;