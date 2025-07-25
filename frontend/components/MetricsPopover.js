import { Popover, Box, Typography, List, ListItem, ListItemIcon, ListItemText, Divider } from '@mui/material';
import TimerIcon from '@mui/icons-material/Timer';
import TokenIcon from '@mui/icons-material/Token';
import ConstructionIcon from '@mui/icons-material/Construction';

export default function MetricsPopover({ message, anchorEl, handleClose }) {
    const open = Boolean(anchorEl);
    const id = open ? 'metrics-popover' : undefined;

    const tokenUsage = message.token_usage || {};
    const toolCalls = message.tool_calls || [];

    return (
        <Popover
            id={id}
            open={open}
            anchorEl={anchorEl}
            onClose={handleClose}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
            <Box sx={{ p: 2, minWidth: 280 }}>
                <Typography variant="subtitle1" gutterBottom>Response Metrics</Typography>
                <List dense>
                    <ListItem>
                        <ListItemIcon><TimerIcon fontSize="small" /></ListItemIcon>
                        <ListItemText primary="Response Time" secondary={`${message.response_time_seconds?.toFixed(2) || 'N/A'} seconds`} />
                    </ListItem>
                    <Divider sx={{ my: 1 }} />
                    <ListItem>
                        <ListItemIcon><TokenIcon fontSize="small" /></ListItemIcon>
                        <ListItemText primary="Prompt Tokens" secondary={tokenUsage.prompt_tokens || '0'} />
                    </ListItem>
                    <ListItem>
                         <ListItemIcon><TokenIcon fontSize="small" color="disabled" /></ListItemIcon>
                        <ListItemText primary="Completion Tokens" secondary={tokenUsage.completion_tokens || '0'} />
                    </ListItem>
                     <ListItem>
                         <ListItemIcon><TokenIcon fontSize="small" color="primary" /></ListItemIcon>
                        <ListItemText primary="Total Tokens" secondary={tokenUsage.total_tokens || '0'} />
                    </ListItem>
                    {toolCalls.length > 0 && (
                        <>
                            <Divider sx={{ my: 1 }} />
                            {toolCalls.map((tool, index) => (
                                <ListItem key={index}>
                                    <ListItemIcon><ConstructionIcon fontSize="small" /></ListItemIcon>
                                    <ListItemText primary="Tool Used" secondary={tool.name} />
                                </ListItem>
                            ))}
                        </>
                    )}
                </List>
            </Box>
        </Popover>
    );
}