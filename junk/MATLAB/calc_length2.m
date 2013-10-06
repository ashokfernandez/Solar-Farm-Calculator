function[length] = calc_length2(lat1, lon1, lat2, lon2)
    R = 6371;
    dlat = (lat2-lat1)*pi/180;
    dlon = (lon2-lon1)*pi/180;
    
    length = R*sqrt((dlat)^2 + (cos(pi*360*(lat1+lat2))*dlon)^2);
end