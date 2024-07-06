function populateColorAndPattern(datasets) {
    datasets.forEach(function(dataset) {
        dataset.data.forEach(function(dataPoint) {
            let patternColor;
            switch(dataPoint.rate) {
                case 'Free':
                case 'Free all day':
                case 'Free Evenings':
                    patternColor = "DarkSeaGreen"
                    break;
                case 'Hourly Rates Apply':
                    patternColor = pattern.draw('dash', '#ff7f0e'); // Orange for Hourly Rates Apply
                    break;
                case '$5 Flat Fee':
                    patternColor = pattern.draw('dot-dash', '#2ca02c'); // Green for $5 Flat Fee
                    break;
                default:
                    patternColor = pattern.draw('diagonal', '#1f77b4'); // Default color
            }
            dataset.backgroundColor = patternColor;
        });
    });

    return datasets;
}