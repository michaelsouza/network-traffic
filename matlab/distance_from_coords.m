function dxy = distance_from_coords(x_lon, x_lat, y_lon, y_lat)
% Reference: Wiki2012 - Geographical distances

% Earth radius
R = 6371.009;    % kilometers
% R = 3958.761; % statute miles
% R = 3440.069; % nautical miles


% conversion to radians
factor = pi/180; % degrees to radians
mean_latitude   = factor * (x_lat + y_lat) / 2;
delta_latitude  = factor * (x_lat - y_lat);
delta_longitude = factor * (x_lon - y_lon);

dxy = R * sqrt(delta_latitude^2+(cos(mean_latitude)*delta_longitude)^2);
