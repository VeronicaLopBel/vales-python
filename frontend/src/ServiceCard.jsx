import { Card, Button, Typography, Box, Stack, Grid } from '@mui/material';
import StatusCounter from './StatusCounter';

function ServiceCard({ name, results, status, onProcess, disabled }) {
  return (
    <Card variant="outlined" sx={{ borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          fullWidth
          size="large"
          sx={{ py: 2, borderRadius: 2, fontWeight: 'bold', textTransform: 'none' }}
          onClick={onProcess}
          disabled={disabled}
        >
          {name}
        </Button>
      </Box>

      <Box sx={{ bgcolor: '#f0f2f5', p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        {results ? (
          <Stack spacing={2}>
            <Typography variant="subtitle2" color="text.secondary">
              Resultados del Proceso:
            </Typography>

            {results?.origen && (
              <>
                <Typography variant="caption" color="text.secondary">
                  Ejecución: {results.origen === 'automatico' ? '⏱ Automática' : '🖐 Manual'}
                </Typography>
                {results?.updated_at && (
                  <Typography variant="caption" color="text.secondary">
                    Última actualización: {results.updated_at}
                  </Typography>
                )}
              </>
            )}

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <StatusCounter label="Descargados" value={results.descargados} />
              </Grid>
              <Grid item xs={6}>
                <StatusCounter label="No Válidos" value={results.no_validos} color="#d32f2f" />
              </Grid>
              <Grid item xs={6}>
                <StatusCounter label="Repetidos" value={results.repetidos} />
              </Grid>
              <Grid item xs={6}>
                <StatusCounter label="Añadidos" value={results.anadidos} color="#2e7d32" />
              </Grid>
            </Grid>
          </Stack>
        ) : (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: 140,
              color: 'text.secondary',
              fontStyle: 'italic',
            }}
          >
            {status || 'Esperando inicio de proceso...'}
          </Box>
        )}
      </Box>
    </Card>
  );
}

export default ServiceCard;