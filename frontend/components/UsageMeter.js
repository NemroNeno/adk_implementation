import { Box, Typography, LinearProgress } from '@mui/material';

export default function UsageMeter({ title, used, limit, unit = '' }) {
    const percentage = limit > 0 ? (used / limit) * 100 : 0;
    
    // Determine color based on usage
    let progressColor = 'primary';
    if (percentage > 90) {
        progressColor = 'error';
    } else if (percentage > 70) {
        progressColor = 'warning';
    }

    return (
        <Box sx={{ my: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2">{title}</Typography>
                <Typography variant="body2" color="text.secondary">
                    {used.toLocaleString()}{unit} / {limit.toLocaleString()}{unit}
                </Typography>
            </Box>
            <LinearProgress variant="determinate" value={percentage} color={progressColor} />
        </Box>
    );
}