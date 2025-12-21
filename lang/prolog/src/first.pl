% first.pl
% Первый контакт с Prolog

human(alex).
human(ari).
human(emme).

mortal(X) :- human(X).
