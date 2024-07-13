function populateColorAndPattern(datasets) {
    datasets.forEach(function(dataset) {
        let backgroundColors = [];

        dataset.data.forEach(function(dataPoint) {
            let patternColor;
            switch(dataPoint.rate) {
                case 'Free':
                case 'Free Evenings':
                case 'Free all day':
                    patternColor = 'DarkSeaGreen';
                    break;
                case 'Hourly Rates Apply':
                case 'Hourly Rates Apply all day':
                    patternColor = pattern.draw('dash', 'orange');
                    break;
                case '$5 Flat Fee':
                case '$5 Flat Fee all day':
                case '$7 Flat Fee':
                case '$7 Flat Fee all day':
                    patternColor = pattern.draw('dot-dash', 'blue');
                    break;
                default:
                    patternColor = pattern.draw('diagonal', 'gray');
            }
            backgroundColors.push(patternColor);
        });

        dataset.backgroundColor = backgroundColors;
    });

    return datasets;
}