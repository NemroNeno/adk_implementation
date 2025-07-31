import { useState } from 'react';
import { Box, Paper, Typography, Avatar, IconButton } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import BarChartIcon from '@mui/icons-material/BarChart';
import MetricsPopover from './MetricsPopover';

export default function ChatMessage({ message }) {
    const isAi = message.role === 'ai';
    const [anchorEl, setAnchorEl] = useState(null);

    const handleMetricsClick = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMetricsClose = () => {
        setAnchorEl(null);
    };

    return (
        // ✅ Added key={message.id}
        <Box key={message.id} sx={{ display: 'flex', justifyContent: isAi ? 'flex-start' : 'flex-end', mb: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: isAi ? 'row' : 'row-reverse', alignItems: 'flex-start', maxWidth: '80%' }}>
                <Avatar sx={{ bgcolor: isAi ? 'primary.main' : 'secondary.main', mx: 1 }}>
                    {isAi ? <SmartToyIcon /> : <AccountCircleIcon />}
                </Avatar>
                <Paper
                    variant="outlined"
                    sx={{ p: 1.5, bgcolor: isAi ? 'background.paper' : 'primary.dark', borderRadius: isAi ? '20px 20px 20px 5px' : '20px 20px 5px 20px' }}
                >
                    <Typography sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {message.content}
                    </Typography>
                </Paper>
                {isAi && message.response_time_seconds && (
                    <>
                        <IconButton size="small" onClick={handleMetricsClick} sx={{ ml: 0.5 }}>
                            <BarChartIcon fontSize="inherit" />
                        </IconButton>
                        <MetricsPopover
                            message={message}
                            anchorEl={anchorEl}
                            handleClose={handleMetricsClose}
                        />
                    </>
                )}
            </Box>
        </Box>
    );
}
