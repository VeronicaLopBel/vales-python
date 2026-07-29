// HeaderPanel.jsx
import { Box, Typography, TextField, Button, Stack } from '@mui/material';

function HeaderPanel({ fromDate, toDate, onChangeFromDate, onChangeToDate, onReset, disabled }) {
  return (
    <Box sx={{ p: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
      <Box>
        <Typography variant="h5" fontWeight="bold">
          Panel de Control
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Rango de proceso seleccionado
        </Typography>
      </Box>

      <Stack direction="row" spacing={2} alignItems="center">
        <TextField
          label="Desde"
          type="date"
          size="small"
          value={fromDate}
          onChange={(e) => onChangeFromDate(e.target.value)}
          disabled={disabled}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          label="Hasta"
          type="date"
          size="small"
          value={toDate}
          onChange={(e) => onChangeToDate(e.target.value)}
          disabled={disabled}
          InputLabelProps={{ shrink: true }}
        />
        <Button variant="outlined" size="small" onClick={onReset} disabled={disabled}>
          Últimos 15 días
        </Button>
      </Stack>
    </Box>
  );
}

export default HeaderPanel;