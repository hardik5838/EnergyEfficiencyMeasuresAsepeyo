<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asepeyo - Energy Savings Measures Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6;
        }
        .chart-container {
            background-color: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }
        h1, h2 {
            font-weight: 700;
        }
    </style>
</head>
<body class="p-4 sm:p-6 md:p-8">

    <div class="max-w-7xl mx-auto">
        <header class="mb-8 text-center">
            <h1 class="text-4xl font-bold text-gray-800">Asepeyo Energy Savings Dashboard</h1>
            <p class="mt-2 text-lg text-gray-600">Visualizing data to prioritize energy efficiency measures.</p>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Chart 1: Investment vs. Payback Period -->
            <div class="chart-container">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Chart 1: The "Quick Wins" Matrix (Investment vs. Payback)</h2>
                <p class="text-sm text-gray-500 mb-4">This chart helps identify the "low-hanging fruit." Projects in the bottom-left quadrant have low investment and a fast payback period, making them ideal starting points.</p>
                <canvas id="investmentPaybackChart"></canvas>
            </div>

            <!-- Chart 4: Effort vs. Impact Grid -->
            <div class="chart-container">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Chart 2: The "Effort vs. Impact" Grid</h2>
                 <p class="text-sm text-gray-500 mb-4">This matrix plots technical simplicity against economic savings to prioritize actions. Focus on the "Just Do It" quadrant for maximum efficiency.</p>
                <canvas id="effortImpactChart"></canvas>
            </div>

            <!-- Chart 3: Overall Most Profitable Measures -->
            <div class="chart-container lg:col-span-2">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Chart 3: Overall Most Profitable Measures</h2>
                <p class="text-sm text-gray-500 mb-4">This chart ranks measures by their total potential annual economic savings across all facilities, highlighting the most financially beneficial initiatives nationwide.</p>
                <canvas id="mostProfitableChart"></canvas>
            </div>

             <!-- Chart 2: Regional Savings Opportunities -->
            <div class="chart-container lg:col-span-2">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Chart 4: Regional Savings Opportunities</h2>
                 <p class="text-sm text-gray-500 mb-4">This chart shows the total potential annual savings for each region, broken down by the type of measure. It helps identify regional patterns and priorities.</p>
                <canvas id="regionalSavingsChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        const data = [
            { region: 'Aragon', facility: 'Asepeyo Zaragoza-Cogullada', recommendation: 'Sistema de gestión energética', savings: 490, investment: 1495, payback: 3.0 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza-Cogullada', recommendation: 'Instalación de temporizador digital en termos eléctricos', savings: 522, investment: 60, payback: 0.1 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza-Cogullada', recommendation: 'Regulación de la temperatura de consigna', savings: 796, investment: 0, payback: 0.0 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza-Cogullada', recommendation: 'Reducción del consumo remanente', savings: 792, investment: 160, payback: 0.2 },
            { region: 'Aragon', facility: 'Asepeyo Teruel', recommendation: 'Ajuste O2 en caldera gasóleo C', savings: 1794, investment: 0, payback: 0.1 },
            { region: 'Aragon', facility: 'Asepeyo Teruel', recommendation: 'Instalador de temporizador digital en termo eléctrico', savings: 404, investment: 70, payback: 0.2 },
            { region: 'Aragon', facility: 'Asepeyo Teruel', recommendation: 'Regulación de la temperatura de consigna', savings: 975, investment: 0, payback: 0.0 },
            { region: 'Aragon', facility: 'Asepeyo Teruel', recommendation: 'Sistema de gestión energética (MONITORIZACIÓN)', savings: 674, investment: 1500, payback: 2.2 },
            { region: 'Aragon', facility: 'Asepeyo Utebo', recommendation: 'Instalación Fotovoltaica', savings: 1026, investment: 1800, payback: 1.8 },
            { region: 'Aragon', facility: 'Asepeyo Utebo', recommendation: 'Instalador de temporizador digital en termo eléctrico', savings: 93, investment: 70, payback: 0.7 },
            { region: 'Aragon', facility: 'Asepeyo Utebo', recommendation: 'Regulación de la temperatura de consigna', savings: 117, investment: 0, payback: 0.0 },
            { region: 'Aragon', facility: 'Asepeyo Utebo', recommendation: 'Sistema de gestión energética. MONITORIZACIÓN', savings: 123, investment: 1500, payback: 12.2 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza', recommendation: 'Instalación Fotovoltaica', savings: 4510, investment: 8550, payback: 1.9 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza', recommendation: 'Instalador de temporizador digital en termo eléctrico', savings: 1743, investment: 1200, payback: 0.2 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza', recommendation: 'Regulación de la temperatura de consigna', savings: 357, investment: 0, payback: 0.0 },
            { region: 'Aragon', facility: 'Asepeyo Zaragoza', recommendation: 'Sistema de gestión energética (MONITORIZACIÓN)', savings: 2086, investment: 1750, payback: 0.8 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Sustitución luminarias a LED', savings: 494, investment: 724, payback: 1.5 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Instalación cortina de aire', savings: 402, investment: 1200, payback: 3.0 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Sistema de gestión energética', savings: 511, investment: 1495, payback: 2.9 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Eliminación energía reactiva', savings: 456, investment: 1597, payback: 3.5 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Instalación de temporizador digital en baño de parafina', savings: 339, investment: 20, payback: 0.1 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Instalación de temporizador digital en termo eléctrico', savings: 312, investment: 20, payback: 0.1 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Regulación de la temperatura de consigna', savings: 724, investment: 0, payback: 0.0 },
            { region: 'Castilla la Mancha', facility: 'Asepeyo Albacete', recommendation: 'Promover la cultura energética', savings: 341, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Badalona Nuevo', recommendation: 'Regulation of the thermostat setpoint', savings: 352, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Badalona Nuevo', recommendation: 'Installation of an air curtain', savings: 987, investment: 1200, payback: 1.2 },
            { region: 'Cataluña', facility: 'Badalona Nuevo', recommendation: 'Energy management system. MONITORING', savings: 418, investment: 1500, payback: 3.6 },
            { region: 'Cataluña', facility: 'Badalona Nuevo', recommendation: 'Promote energy culture', savings: 557, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Asepeyo Berga', recommendation: 'Promote energy culture', savings: 354, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Asepeyo Berga', recommendation: 'Temperature regulation', savings: 452, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Asepeyo Berga', recommendation: 'Reduce standby consumption', savings: 426, investment: 56, payback: 0.1 },
            { region: 'Cataluña', facility: 'Asepeyo Berga', recommendation: 'Energy management system', savings: 532, investment: 1795, payback: 3.4 },
            { region: 'Cataluña', facility: 'Asepeyo Caspe', recommendation: 'Energy management system. MONITORING', savings: 1445, investment: 1500, payback: 1.2 },
            { region: 'Cataluña', facility: 'Asepeyo Caspe', recommendation: 'Setpoint temperature regulation', savings: 824, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Asepeyo Caspe', recommendation: 'Air curtain installation', savings: 2310, investment: 1200, payback: 0.5 },
            { region: 'Cataluña', facility: 'Asepeyo Caspe', recommendation: 'Heat recovery units', savings: 5504, investment: 13500, payback: 2.5 },
            { region: 'Cataluña', facility: 'Asepeyo Cerdanyola', recommendation: 'Energy management system. MONITORING', savings: 548, investment: 1500, payback: 2.7 },
            { region: 'Cataluña', facility: 'Asepeyo Cerdanyola', recommendation: 'Setpoint temperature regulation', savings: 335, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Asepeyo Cerdanyola', recommendation: 'Air curtain installation', savings: 942, investment: 1200, payback: 1.3 },
            { region: 'Cataluña', facility: 'Asepeyo Cerdanyola', recommendation: 'Digital timer installation on electric water heater', savings: 296, investment: 70, payback: 0.2 },
            { region: 'Cataluña', facility: 'Asepeyo Figueres', recommendation: 'Photovoltaic Installation', savings: 1910, investment: 4050, payback: 2.0 },
            { region: 'Cataluña', facility: 'Asepeyo Figueres', recommendation: 'Energy management system', savings: 359, investment: 1500, payback: 4.2 },
            { region: 'Cataluña', facility: 'Asepeyo Figueres', recommendation: 'Promote energy culture', savings: 478, investment: 0, payback: 0.0 },
            { region: 'Cataluña', facility: 'Asepeyo Figueres', recommendation: 'Digital timer installation on electric water heater', savings: 130, investment: 34, payback: 0.0 },
            { region: 'Madrid', facility: 'Asepeyo Alcobendas', recommendation: 'Sistema de gestión energética', savings: 533, investment: 1500, payback: 2.8 },
            { region: 'Madrid', facility: 'Asepeyo Alcobendas', recommendation: 'Promover la cultura energética', savings: 355, investment: 0, payback: 0.0 },
            { region: 'Madrid', facility: 'Asepeyo Alcobendas', recommendation: 'Instalación Fotovoltaica', savings: 5125, investment: 8550, payback: 1.7 },
            { region: 'Madrid', facility: 'Asepeyo Alcobendas', recommendation: 'Mejora en el control actual (iluminación)', savings: 549, investment: 1579, payback: 2.9 },
            { region: 'Madrid', facility: 'Asepeyo Alcobendas', recommendation: 'Eliminación de la energía reactiva', savings: 820, investment: 850, payback: 1.0 },
            { region: 'Murcia', facility: 'Asepeyo Cartagena', recommendation: 'Promover la cultura energética', savings: 148, investment: 0, payback: 0.0 },
            { region: 'Murcia', facility: 'Asepeyo Cartagena', recommendation: 'Instalación cortina de aire', savings: 331, investment: 1200, payback: 3.6 },
            { region: 'Murcia', facility: 'Asepeyo Cartagena', recommendation: 'Sistema de gestión energética', savings: 223, investment: 1295, payback: 5.8 },
            { region: 'Murcia', facility: 'Asepeyo Cartagena', recommendation: 'Instalación de temporizador digital en baño de parafina', savings: 322, investment: 20, payback: 0.1 },
            { region: 'Murcia', facility: 'Asepeyo Cartagena', recommendation: 'Mejora en el control de la iluminación', savings: 177, investment: 336, payback: 1.9 },
            { region: 'Navarra', facility: 'Asepeyo Pamplona', recommendation: 'Instalación de temporizador digital en termo eléctrico', savings: 319, investment: 68, payback: 0.2 },
            { region: 'Navarra', facility: 'Asepeyo Pamplona', recommendation: 'Reducción del consumo remanente', savings: 684, investment: 170, payback: 0.3 },
            { region: 'Navarra', facility: 'Asepeyo Pamplona', recommendation: 'Sistema de gestión energética', savings: 863, investment: 1500, payback: 1.7 },
            { region: 'Navarra', facility: 'Asepeyo Pamplona', recommendation: 'Promover la cultura energética', savings: 1151, investment: 0, payback: 0.0 },
        ];

        // Helper function to categorize measures by technical simplicity
        function getTechnicalSimplicity(recommendation) {
            const rec = recommendation.toLowerCase();
            if (rec.includes('cultura') || rec.includes('consigna') || rec.includes('temperature regulation')) {
                return 'Very Simple';
            } else if (rec.includes('temporizador') || rec.includes('timer') || rec.includes('remanente') || rec.includes('standby')) {
                return 'Simple';
            } else if (rec.includes('led') || rec.includes('cortina de aire') || rec.includes('air curtain') || rec.includes('control')) {
                return 'Moderate';
            } else if (rec.includes('fotovoltaica') || rec.includes('photovoltaic') || rec.includes('gestión') || rec.includes('management system')) {
                return 'Complex';
            }
            return 'Moderate';
        }

        const effortLevels = ['Very Simple', 'Simple', 'Moderate', 'Complex'];

        // Helper function to generate colors
        const colorPalette = [
            '#3b82f6', '#10b981', '#f97316', '#8b5cf6', '#ec4899', '#ef4444', '#f59e0b', '#14b8a6', '#6366f1', '#d946ef'
        ];
        const regionColorMap = {};
        const measureColorMap = {};
        let colorIndex = 0;
        let measureColorIndex = 0;

        const allRegions = [...new Set(data.map(d => d.region))];
        allRegions.forEach(region => {
            regionColorMap[region] = colorPalette[colorIndex % colorPalette.length];
            colorIndex++;
        });

        const allMeasures = [...new Set(data.map(d => d.recommendation))];
        allMeasures.forEach(measure => {
            measureColorMap[measure] = colorPalette[measureColorIndex % colorPalette.length];
            measureColorIndex++;
        });


        // --- Chart 1: Investment vs. Payback ---
        const investmentPaybackCtx = document.getElementById('investmentPaybackChart').getContext('2d');
        const investmentPaybackData = {
            datasets: data.map(d => ({
                label: `${d.facility}: ${d.recommendation}`,
                data: [{ x: d.investment, y: d.payback }],
                backgroundColor: regionColorMap[d.region] + 'b3', // Add alpha for transparency
                borderColor: regionColorMap[d.region],
                borderWidth: 1,
                pointRadius: 6,
                pointHoverRadius: 8
            }))
        };
        new Chart(investmentPaybackCtx, {
            type: 'scatter',
            data: investmentPaybackData,
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: { display: true, text: 'Investment (€)', font: { size: 14 } }
                    },
                    y: {
                        title: { display: true, text: 'Payback Period (Years)', font: { size: 14 } }
                    }
                }
            }
        });

        // --- Chart 2: Effort vs. Impact ---
        const effortImpactCtx = document.getElementById('effortImpactChart').getContext('2d');
        const effortImpactData = {
            datasets: data.map(d => ({
                label: `${d.facility}: ${d.recommendation}`,
                data: [{ 
                    x: effortLevels.indexOf(getTechnicalSimplicity(d.recommendation)), 
                    y: d.savings 
                }],
                backgroundColor: regionColorMap[d.region] + 'b3',
                borderColor: regionColorMap[d.region],
                borderWidth: 1,
                pointRadius: 6,
                pointHoverRadius: 8
            }))
        };
        new Chart(effortImpactCtx, {
            type: 'scatter',
            data: effortImpactData,
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Technical Simplicity (Effort)', font: { size: 14 } },
                        min: -0.5,
                        max: 3.5,
                        ticks: {
                            stepSize: 1,
                            callback: function(value, index, values) {
                                return effortLevels[value];
                            }
                        }
                    },
                    y: {
                        title: { display: true, text: 'Annual Economic Savings (€)', font: { size: 14 } }
                    }
                },
                annotation: {
                    annotations: {
                        line1: { type: 'line', xMin: 1.5, xMax: 1.5, borderColor: 'rgba(0,0,0,0.2)', borderWidth: 2 },
                        line2: { type: 'line', yMin: 2000, yMax: 2000, borderColor: 'rgba(0,0,0,0.2)', borderWidth: 2 },
                        label1: { type: 'label', xValue: 0.5, yValue: 5000, content: 'Just Do It!', font: { size: 16, weight: 'bold' }, color: 'rgba(0,0,0,0.6)' },
                        label2: { type: 'label', xValue: 2.5, yValue: 5000, content: 'Strategic Projects', font: { size: 16, weight: 'bold' }, color: 'rgba(0,0,0,0.6)' },
                        label3: { type: 'label', xValue: 0.5, yValue: 500, content: 'Fill-ins', font: { size: 16, weight: 'bold' }, color: 'rgba(0,0,0,0.6)' },
                        label4: { type: 'label', xValue: 2.5, yValue: 500, content: 'Re-evaluate', font: { size: 16, weight: 'bold' }, color: 'rgba(0,0,0,0.6)' },
                    }
                }
            }
        });

        // --- Chart 3: Most Profitable Measures ---
        const profitableMeasures = {};
        data.forEach(d => {
            const measure = d.recommendation.replace('(MONITORIZACIÓN)', '').replace('. MONITORIZACIÓN', '').trim();
            if (!profitableMeasures[measure]) {
                profitableMeasures[measure] = 0;
            }
            profitableMeasures[measure] += d.savings;
        });
        const sortedMeasures = Object.entries(profitableMeasures).sort(([, a], [, b]) => b - a);
        const mostProfitableCtx = document.getElementById('mostProfitableChart').getContext('2d');
        new Chart(mostProfitableCtx, {
            type: 'bar',
            data: {
                labels: sortedMeasures.map(d => d[0]),
                datasets: [{
                    label: 'Total Annual Economic Savings (€)',
                    data: sortedMeasures.map(d => d[1]),
                    backgroundColor: sortedMeasures.map(d => measureColorMap[d[0]] + 'b3'),
                    borderColor: sortedMeasures.map(d => measureColorMap[d[0]]),
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { title: { display: true, text: 'Total Annual Economic Savings (€)', font: { size: 14 } } }
                }
            }
        });

        // --- Chart 4: Regional Savings ---
        const regionalSavings = {};
        data.forEach(d => {
            if (!regionalSavings[d.region]) {
                regionalSavings[d.region] = {};
            }
            const measure = d.recommendation.replace('(MONITORIZACIÓN)', '').replace('. MONITORIZACIÓN', '').trim();
            if (!regionalSavings[d.region][measure]) {
                regionalSavings[d.region][measure] = 0;
            }
            regionalSavings[d.region][measure] += d.savings;
        });
        const regionalCtx = document.getElementById('regionalSavingsChart').getContext('2d');
        const regionalDatasets = allMeasures.map(measure => {
            return {
                label: measure,
                data: allRegions.map(region => regionalSavings[region]?.[measure] || 0),
                backgroundColor: measureColorMap[measure],
            }
        });

        new Chart(regionalCtx, {
            type: 'bar',
            data: {
                labels: allRegions,
                datasets: regionalDatasets
            },
            options: {
                plugins: {
                    title: { display: false },
                },
                responsive: true,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, title: { display: true, text: 'Total Annual Economic Savings (€)', font: { size: 14 } } }
                }
            }
        });
    </script>
</body>
</html>

