import { Box, Typography } from '@mui/material';

function StatusCounter({ label, value, color }) {
  return (
    <Box sx={{ p: 1, textAlign: 'center', borderRadius: 2, bgcolor: '#ffffff', boxShadow: 'inset 0 0 0 1px rgba(15,23,42,0.06)' }}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography variant="h4" fontWeight="bold" color={color || 'primary'}>
        {value}
      </Typography>
    </Box>
  );
}

export default StatusCounter;
