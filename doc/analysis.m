%% Parameters
A1 = 28; A3 = 28;
A2 = 32; A4 = 32;
A = [A1 A2 A3 A4];

a1 = 0.071; a3 = 0.071;
a2 = 0.057; a4 = 0.057;
a = [a1 a2 a3 a4];

k1 = 3.33; k2 = 3.33;
g = 981;

gamma1 = 0.4;
gamma2 = 0.2;

%% Linearization point
h0 = [40 40 40 40];
u0 = [0 0];

%% Matrices from the guide TODO: Calculate them ourselves
T = A./a .* sqrt(2*h0/g);

F = diag(-1./T);
F(1,3) = A(3)/A(1)/T(3);
F(2,4) = A(4)/A(2)/T(4);

G = zeros(4,2);
G(1,1) = gamma1*k1/A1;
G(2,2) = gamma2*k2/A2;
G(3,2) = (1-gamma2)*k2/A3;
G(4,1) = (1-gamma1)*k1/A4;

%% Is the linearized system controllable?
unco = length(A) - rank(ctrb(F, G));
unco == 0