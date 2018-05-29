%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Berechnet das ensemblegemittelte g2_E mit Hilfe der Bruteforce Methode
% bei variablem Anfang
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Dazu wird zuerst die Intensitätsautokorrelationsfunktion(IAKF) g2_T für 
% jeden Speckle einzeln berechnet und dann mit Hilfe der Bruteforcemethode
% g2_E berechnet

%Eingabe: 
%specklemeanint; Mittlere Speckleintensität für jeden einzelnen Speckle
%startwert; Entspricht der Wartezeit
%corrtime;  Dauer der Korrelation (in Bildern)


%Ausgabe:
%g2_T;      IAKF für jeden Speckle
%g2_E;      ensemblegemittelte IAKF
%meanint_T; zeitlich gemittelte Intensität für jeden Speckle
%meanint_E; ensemblegemittelte Intensität über die zeitlich gemittelten 
%           Intensitäten der Speckle
%f_E;       Dichteautokorrelationsfunktion des Ensembles
%g2minus1_e: f_E^2

%Bestimmt anhand der mitteleren Speckleintensitäten die Anzahl der Bilder
%sowie die Anzahl der Speckle
tic
temp=size(specklemeanint);
bilder=temp(1,1);
speckle=temp(1,2);
clear('temp');
startwert=0;
endwert=corrtime+startwert;
%Länge der auszuwertenden Sequenz
laenge=endwert-startwert;

%Berechnet die zeitgemittelte Intensität für jeden Speckle
meanint_T_wait_speckle=zeros(1,speckle);
for i=1:speckle
    meanint_T_wait_speckle(1,i)=mean(specklemeanint(startwert+1:endwert,i));
end

%For-Schleife zur Berechnung von g2_T für jeden Speckle
g2_T=zeros(laenge,speckle);
for i=1:speckle
    akftemp=xcorr(specklemeanint(startwert+1:endwert,i), 'unbiased');
    g2_T(:,i)=akftemp(laenge:2*laenge-1,1)/meanint_T_wait_speckle(1,i)^2;
    clear('akftemp');
end

%Berechnet meanint_E aus meanint_T
meanint_E=sum(meanint_T_wait_speckle);
%Berechnet mit der Bruteforce-Methode g2_E
summe=zeros(laenge,1);
for i=1:speckle
    summe=summe+g2_T(:,i)*(meanint_T_wait_speckle(1,i))^2;
end
g2_E=(summe*speckle)/(meanint_E)^2;
g2minus1_E=(g2_E-1)/(g2_E(1,1)-1);
%Dichteautokorrelationsfunktion des Ensembles mit Hilfe der
%Siegert-Relation
f_E=sqrt((g2_E-1)/(g2_E(1,1)-1));
%g2_T_60k=g2_T;
beta_wait7min=g2_T(1,:)-1;
%Berechnet g2minus1
g2minus1=zeros(laenge,speckle);
for i=1:speckle
    g2minus1(:,i)=(g2_T(:,i)-1)/(g2_T(1,i)-1);
end
%meanint_T_wait_30k=meanint_T;
%Löscht überflüssige Variablen
%clearvars -except specklemeanint f_E g2minus1_E g2_E g2_T f_E_speckle meanint_T_wait_speckle
toc