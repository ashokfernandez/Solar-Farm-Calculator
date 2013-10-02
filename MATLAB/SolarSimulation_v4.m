% Author: Darren O'Neill    Date: 20/09/2013
% This script simulates a solar farm to obtain the effeciency of a given
% location

% Input Variables--------------------------------------------------------%

%-------------------Solar Panels-------------------------------%

panelVoltage = 30.5; % Voltage of the panel at maximum power point
panelEff = 0.15; % Solar panel effeciency (typically 15-18 %)
panelDegRate = 0.4; % Rate at which the solar panel degradates (% per year)
panelArea = 1.63; % Panel area (m^2)


% Finacial
panelCost = 50; % Cost of the single panel
panelDepRate = 20; % Panel depreciation rate (% per year)


%------------------Solar Module--------------------------------%

moduleNum = 20; % Number of solar panels in a module

solarVoltage = panelVoltage*moduleNum;


%----------------Array Parameters------------------------------%

arrayModuleNum = 7; % Number of modules that make up an array (modlues are in parrallel)
arrayAngle = 45; % Angle from panel to horizontal
useOptimumAngle = 1;

%-----------------------DC cables------------------------------%

DCdiameter = 20; % DC cable diameter in mm
DCcableMaterial = 'Cu'; % DC cable conductor material
DCcableLength = 100; % DC cable length in meters

% Finacial
DCcostPerMeter = 100; % Cost of DC cable per meter
DCDepRate = 6; % DC cable depreciation rate (% per year)

%---------------------Inverter---------------------------------%

InvPowerFactor = 0.95; % Power factor of the output of the inverter
InvEff = 0.85; % Inverter effeciency (typicall loss 4-15 %)
InvOutVolt = 400; % Output voltage of the inverter (line to line)

% Finicial
InvCost = 10000; % Cost of the inverter/s
InvDepRate = 7; % Inverter depreciation rate (% per year)

%--------------------Inv-Tx Lines (AC1 Cables)-----------------%

AC1Diameter = 6; % Inv-Tx line cable diameter
AC1Material = 'Al'; % Inv-Tx cable material
AC1Length = 100; % Length of the Inv-Tx cable

% Finicial

AC1Cost = 100; % Cost of cable per meter
AC1DepRate = 6; % Inv-Tx cable depreciation rate (% per year)

%-----------------Transformer----------------------------------%

TxOutVolt = 11e3; % Transformer secondary voltage
TxEff = 0.95; % Transformer efficiency
TxRating = 3; % MVA rating

% Financial

TxCost = 1000000; % Cost of the transformer
TxDepRate = 6; % Transformer depreciation rate (% per year)
TxScrap = 30000; % Transformer scrap value

%-----------------GXP Lines------------------------------------%

AC2StrandNum = 5; % Number of strands in ACC or ACSR cable
AC2StrandDiameter = 2; % Strand diameter in mm
AC2Material = 'Al'; % Strand material
specifyLength = 0;
AC2Length = 0;



% Finacial
AC2Cost = 100; % Cost of SINGLE cable per meter
TranLineCost = 1000; % Cost of building the transmission line per kilometer
AC2DepRate = 6; % Depreciation rate of the GXP line (% per year)

%----------------Site Parameters--------------------------------%

numTx = 3; % Number of transfromers
numArrays = 30; % Number of solar arrays
numCircuitBreakers = 15; % Number of circuit breakers
numInverters = 10; % Number of inverters

siteLat = 27.67; % Site latitude
siteLon = 85.42; % Site longitude
GXPLat = 27.70; % GXP latitude
GXPLon = 85.32; % GXP longitude

temp = zeros(1,365);

for I = 1:365
    temp(I) = -0.0005*I^2 + 0.2138*I + 2.1976;
end

irradiance = zeros(1,365); % Average solar irradiance perpendicular to the ground in W/m^2

for I = 1:365
    irradiance(I) = -0.021*I^2 + 8.5246*I + 74.471; % Formula calculated from data in source
end

sunlightHours = zeros(1,365); % Number of sunlight hours per day (could turn into a function)

for I = 1:365
    sunlightHours(I) = -5e-11*I^5 + 4e-8*I^4 -1e-5*I^3 + 6e-4*I^2 + 2.99e-2*I + 6.0658;
end

siteArea = 1; % Site area in km^2

% Finicial
breakerCost = 10000; % Cost of each circuit breakers
breakerDepRate = 6; % Circuit breaker depreciation rate (% per year)
landPrice = 100000; % Cost per km^2 of land
landAppRate = 3; % Land appreciation rate (% per year)

%------------------------Other Finicial-------------------------%

maintainceBudget = 100000; % Maintaince budget per year
labourCosts = 500000; % Intial labour costs to build site
miscCapitalCosts = 500000;% Misc initial capital costs
miscDepRate = 8; % Misc depreciation rate (% per year)
buyBackRate = 0.25; % Selling rate of power ($/kWh)

%--------------------Simulation Details------------------------%

findPayBack = 0; % Find the payback period

startDay = 13;
startMonth = 'November';
startYear = 2013;

endDay = 28;
endMonth = 'February';
endYear = 2016;

months = {'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'};
daysMonths = [0, 28, 59, 89, 120, 150, 181, 212, 242, 273, 303, 334];

bindex = find(ismember(months, startMonth));

dindex = find(ismember(months, endMonth));

beginDay = startDay + daysMonths(bindex);

if (findPayBack == 0)
    simLength = 365*(endYear-startYear-1) + (365 - beginDay) + daysMonths(dindex) + endDay;
else
    simLength = 50*365;
end
%------------------------------------------------------------------------%


if (specifyLength == 0)
        AC2Length = calc_length2(siteLat, siteLon, GXPLat, GXPLon);
end

% Solar Panel calcs

% Working the irradiance on the panel as a function of the day
optimumAngle = calc_optimumAngle(irradiance, siteLat);

panelIrr = zeros(1,365);

if (useOptimumAngle == 1)
    usedAngle = optimumAngle;
else
    usedAngle = arrayAngle;
end

for I = 1:365
        a = 90 - siteLat + 23.45*sind(360/365*(284 + I));
        panelIrr(I) = irradiance(I)*sind(a + usedAngle)/sind(a);
end

% plot(panelIrr)



% Initialise data arrays

solarOutput = zeros(1,simLength);
DCoutput = zeros(1,simLength);
invOutput = zeros(1,simLength);
AC1Output = zeros(1,simLength);
TxOut = zeros(1,simLength);
AC2Output = zeros(1,simLength);
totalEffeciency = zeros(1,simLength);
elecEff = zeros(1,simLength);
energyOutput = zeros(1,simLength);

capitalWorth = zeros(1,50);


day = beginDay;
days = zeros(1,simLength);
year = 0;

for I = 1:simLength
    
    days(I) = day;
   
    %---------------------Power/Energy Analysis---------------------------%
    
    numPanels = moduleNum*arrayModuleNum*numArrays;
        
    totalArea = panelArea*numPanels;
    solarOutput(I) = panelIrr(day)*totalArea*panelEff*(1-panelDegRate/(100*365)*I);
    
    % DC cable calcs
    
    DCresistance = calc_resistance(DCcableMaterial, temp(day), DCdiameter, DCcableLength);
    
    DCcurrent = solarOutput(I)/solarVoltage;
    
    DCloss = 2*DCcurrent^2*DCresistance;
    
    DCEff = (solarOutput(I) - DCloss)/solarOutput(I);
    
    DCoutput(I) = solarOutput(I) - DCloss;
    
    % Inverter calcs
    
    invOutput(I) = DCoutput(I) * InvEff;
    
    % 3 P AC Cables to Tx calcs
    
    AC1resistance = calc_resistance(AC1Material, temp(day), AC1Diameter, AC1Length);
    
    IAC1 = invOutput(I)/(sqrt(3)*InvPowerFactor*InvOutVolt);
    
    AC1loss = 3*IAC1^2*AC1resistance;
    
    AC1Output(I) = invOutput(I) - AC1loss;
    
    % Transformer calcs
    
    TxOut(I) = AC1Output(I)*TxEff;
    
    % 3 P tranmission lines to GXP calcs
    
    strandResistance = calc_resistance(AC2Material, temp(day), AC2StrandDiameter, AC2Length);
    
    totalResistance = strandResistance/AC2StrandNum;
    
    IAC2 = TxOut(I)/(sqrt(3)*InvPowerFactor*TxOutVolt);
    
    AC2loss = 3*IAC2^2*totalResistance;
    
    AC2Output(I) = TxOut(I) - AC2loss;
    
    totalEffeciency(I) = AC2Output(I)/(panelIrr(day)*totalArea)*100;
    
    elecEff(I) = AC2Output(I)/solarOutput(I)*100;
    
    energyOutput(I) = AC2Output(I)*sunlightHours(day); % Daily output in Wh
    
    %-------------Finicial-----------------------------------------------%
    if (day == startDay) && (I ~= 1)
        % Calculate finicial data
        year = year + 1;
        capitalWorth = landPrice*siteArea*(1+landAppRate/100)^year + ...
            panelCost*numPanels*(1-panelDepRate/100)^year + DCcostPerMeter*DCcableLength*(1-DCDepRate/100)^year ...
            + InvCost*numInverters*(1-InvDepRate/100)^year + AC1Cost*AC1Length*(1-AC1DepRate/100)^year ...
            + TxCost*(1-TxDepRate/100)^2 + (AC2Cost + TranLineCost)*AC2Length*(1-AC2DepRate/100)^year ...
            + miscCapitalCosts*(1-miscDepRate/100)^year;
        expenses = maintainceBudget*year + labourCosts;
        totalIncome = sum(energyOutput)/1000*buyBackRate;
        if (totalIncome > (expenses + capitalWorth(1)))
            break;
        end
    elseif (I == 1)
        % Initial Capital Worth
        capitalWorth(year + 1) = landPrice*siteArea + panelCost*numPanels ...
            + DCcostPerMeter*DCcableLength + InvCost*numInverters + ...
            AC1Cost*AC1Length + TxCost + (AC2Cost + TranLineCost)*AC2Length ...
            + miscCapitalCosts;
    end
    
    %---------------------------------------------------------------------%
    
    if (day < 365)
        day = day + 1;
    else
        day = 1;
    end
        
end

% income = sum(energyOutput)*buyBackRate;
plot(solarOutput)
hold on;
plot(DCoutput)
hold off;
