function[resistance] = calc_resistance(mat, temp, diameter, length)

     if (strcmp('Cu',mat))
        p = 1.68e-8*(1 + 0.00362*(temp-20));
     elseif (strcmp('Al',mat))
        p = 2.82e-8*(1 + 0.0039*(temp-20));
     end
     
     area = pi/4*(diameter*1e-3)^2;
     
     resistance = p*length/area;
end
