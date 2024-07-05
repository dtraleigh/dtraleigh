function getEasternStandardTimeHour() {
    const now = new Date();
    const options = { timeZone: 'America/New_York', hour12: false, hour: '2-digit' };
    const estTimeString = now.toLocaleString('en-US', options);
    return estTimeString;
}