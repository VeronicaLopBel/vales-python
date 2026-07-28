import { Box, Typography } from '@mui/material';

function HeaderPanel({ fromDate, toDate }) {
  return (
    <Box sx={{ p: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Box>
        <Typography variant="h5" fontWeight="bold">
          Panel de Control
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Rango de proceso: {fromDate} – {toDate}
        </Typography>
      </Box>
      <Typography variant="caption" color="text.secondary">
        Última actualización al iniciar el proceso
      </Typography>
    </Box>
  );
}

export default HeaderPanel;
