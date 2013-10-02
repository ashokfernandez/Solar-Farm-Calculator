function[opAngle] = calc_optimumAngle(directIrr, siteLat)

testAngle = 0:0.1:90;
angleLength = length(testAngle);
testPanelIrr = zeros(angleLength,365);
meanIrr = zeros(1,angleLength);

for I = 1:angleLength
    for J = 1:365
        a = 90 - siteLat + 23.45*sind(360/365*(284 + J));
        testPanelIrr(I,J) = directIrr(J)*sind(a + testAngle(I))/sind(a);
    end
    meanIrr(I) = mean(testPanelIrr(I,:));
end

% for I = 1:10:angleLength
%     plot(testPanelIrr(I,:))
%     hold on;
% end
% hold off;

[value, ind] = max(meanIrr);

opAngle = testAngle(ind);

end