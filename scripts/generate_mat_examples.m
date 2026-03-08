%% generate_mat_examples.m
% Generates reference *.mat files covering all format variants that
% MATHandler is expected to read.  Run this script once in MATLAB to
% (re-)create thesave(fullfile(out_dir, 'mat_v7_struct_timeseries.mat'), 'signals', '-v7', '-nocompression');fixtures used by the Python test suite.
%
% Output files (written to the same directory as this script):
%
%   mat_v7_flat_signals.mat          – v7,   flat signal arrays + timestamps
%   mat_v73_flat_signals.mat         – v7.3, flat signal arrays + timestamps
%   mat_v7_struct_signals.mat        – v7,   struct of signal arrays + timestamps
%   mat_v73_struct_signals.mat       – v7.3, struct of signal arrays + timestamps
%   mat_v7_flat_timeseries.mat       – v7,   flat MATLAB timeseries objects
%   mat_v73_flat_timeseries.mat      – v7.3, flat MATLAB timeseries objects
%   mat_v7_struct_timeseries.mat     – v7,   struct of MATLAB timeseries objects
%   mat_v73_struct_timeseries.mat    – v7.3, struct of MATLAB timeseries objects

out_dir = fileparts(mfilename('fullpath'));

%% -----------------------------------------------------------------------
%  Shared signal data
%  sig_a: scalar per timestep, uniform 10 Hz sampling
%  sig_b: 1-D array (size 3) per timestep, uniform 10 Hz sampling
%  sig_c: scalar per timestep, non-uniform / faster 20 Hz sampling
%         (used only in timeseries variants where mixed rates are possible)
% -----------------------------------------------------------------------

% --- uniform 10 Hz ---
fs10      = 10;                          % Hz
t10       = (0 : 1/fs10 : 1)';          % 0 … 1 s  (11 samples)

% base waveforms (double) – cast to target dtype per section below
sig_a_f64 = sin(2*pi*1*t10);            % double  scalar
sig_a_f32 = single(sig_a_f64);          % single  scalar
sig_a_i8  = int8(127 * sig_a_f64);      % int8    scalar
sig_a_u8  = uint8(127 + int8(127 * sig_a_f64)); % uint8 scalar (shifted to [0,254])
sig_a_i16 = int16(1000 * sig_a_f64);    % int16   scalar
sig_a_u16 = uint16(1000 + int16(1000 * sig_a_f64)); % uint16 scalar
sig_a_i32 = int32(1e6 * sig_a_f64);     % int32   scalar
sig_a_u32 = uint32(1e6 + int32(1e6 * sig_a_f64));   % uint32 scalar
sig_a_i64 = int64(1e9 * sig_a_f64);     % int64   scalar
sig_a_u64 = uint64(1e9 + int64(1e9 * sig_a_f64));   % uint64 scalar
sig_a_log = sig_a_f64 > 0;              % logical scalar

sig_b_f64 = [sin(2*pi*1*t10), ...
             cos(2*pi*1*t10), ...
             sin(2*pi*2*t10)];          % double  array [11 x 3]
sig_b_f32 = single(sig_b_f64);          % single  array
sig_b_i32 = int32(1e6 * sig_b_f64);     % int32   array

% --- uniform 20 Hz (sig_c, used in timeseries variants for mixed-rate demo) ---
fs20      = 20;
t20       = (0 : 1/fs20 : 1)';          % 0 … 1 s  (21 samples)
sig_c_f64 = cos(2*pi*2*t20);            % double  scalar
sig_c_f32 = single(sig_c_f64);          % single  scalar

%% =======================================================================
%  1.  FLAT SIGNAL STRUCTURE
%      Variables at top level: timestamps (Nx1), one signal per dtype
% =======================================================================
timestamps = t10;   %#ok<NASGU>
sig_a_f64  = sig_a_f64; %#ok<ASGSL>
sig_a_f32  = sig_a_f32; %#ok<ASGSL>
sig_a_i8   = sig_a_i8;  %#ok<ASGSL>
sig_a_u8   = sig_a_u8;  %#ok<ASGSL>
sig_a_i16  = sig_a_i16; %#ok<ASGSL>
sig_a_u16  = sig_a_u16; %#ok<ASGSL>
sig_a_i32  = sig_a_i32; %#ok<ASGSL>
sig_a_u32  = sig_a_u32; %#ok<ASGSL>
sig_a_i64  = sig_a_i64; %#ok<ASGSL>
sig_a_u64  = sig_a_u64; %#ok<ASGSL>
sig_a_log  = sig_a_log; %#ok<ASGSL>
sig_b_f64  = sig_b_f64; %#ok<ASGSL>
sig_b_f32  = sig_b_f32; %#ok<ASGSL>
sig_b_i32  = sig_b_i32; %#ok<ASGSL>

save(fullfile(out_dir, 'mat_v7_flat_signals.mat'), ...
    'timestamps', ...
    'sig_a_f64', 'sig_a_f32', 'sig_a_i8', 'sig_a_u8', ...
    'sig_a_i16', 'sig_a_u16', 'sig_a_i32', 'sig_a_u32', ...
    'sig_a_i64', 'sig_a_u64', 'sig_a_log', ...
    'sig_b_f64', 'sig_b_f32', 'sig_b_i32', '-v7', '-nocompression');
save(fullfile(out_dir, 'mat_v73_flat_signals.mat'), ...
    'timestamps', ...
    'sig_a_f64', 'sig_a_f32', 'sig_a_i8', 'sig_a_u8', ...
    'sig_a_i16', 'sig_a_u16', 'sig_a_i32', 'sig_a_u32', ...
    'sig_a_i64', 'sig_a_u64', 'sig_a_log', ...
    'sig_b_f64', 'sig_b_f32', 'sig_b_i32', '-v7.3');
fprintf('[OK] flat signal files written\n');

clearvars timestamps

%% =======================================================================
%  2.  STRUCT OF SIGNAL ARRAYS  (Simulink-style)
%      data.timestamps  (Nx1 double)
%      data.sig_*       one field per dtype
% =======================================================================
data.timestamps = t10;
data.sig_a_f64  = sig_a_f64;
data.sig_a_f32  = sig_a_f32;
data.sig_a_i8   = sig_a_i8;
data.sig_a_u8   = sig_a_u8;
data.sig_a_i16  = sig_a_i16;
data.sig_a_u16  = sig_a_u16;
data.sig_a_i32  = sig_a_i32;
data.sig_a_u32  = sig_a_u32;
data.sig_a_i64  = sig_a_i64;
data.sig_a_u64  = sig_a_u64;
data.sig_a_log  = sig_a_log;
data.sig_b_f64  = sig_b_f64;
data.sig_b_f32  = sig_b_f32;
data.sig_b_i32  = sig_b_i32; %#ok<STRNU>

save(fullfile(out_dir, 'mat_v7_struct_signals.mat'),  'data', '-v7', '-nocompression');
save(fullfile(out_dir, 'mat_v73_struct_signals.mat'), 'data', '-v7.3');
fprintf('[OK] struct signal files written\n');

clearvars data

%% =======================================================================
%  3.  FLAT TIMESERIES
%      Each top-level variable is a struct with Time and Data fields.
%      sig_a_* @ 10 Hz, sig_c_* @ 20 Hz → mixed sample rates.
%      sig_b_* demonstrate array-per-timestep with non-double dtypes.
%      Note: plain structs are used instead of MATLAB timeseries objects
%      so that scipy (v7) and h5py (v7.3) can read them without a MATLAB
%      OOP deserialiser.
% =======================================================================
ts_sig_a_f64 = struct('Time', t10, 'Data', sig_a_f64);
ts_sig_a_f32 = struct('Time', t10, 'Data', sig_a_f32);
ts_sig_a_i32 = struct('Time', t10, 'Data', sig_a_i32);
ts_sig_a_u16 = struct('Time', t10, 'Data', sig_a_u16);
ts_sig_a_i8  = struct('Time', t10, 'Data', sig_a_i8);
ts_sig_a_log = struct('Time', t10, 'Data', sig_a_log);
ts_sig_b_f32 = struct('Time', t10, 'Data', sig_b_f32);
ts_sig_b_i32 = struct('Time', t10, 'Data', sig_b_i32);
ts_sig_c_f64 = struct('Time', t20, 'Data', sig_c_f64); % 20 Hz
ts_sig_c_f32 = struct('Time', t20, 'Data', sig_c_f32); % 20 Hz

save(fullfile(out_dir, 'mat_v7_flat_timeseries.mat'), ...
    'ts_sig_a_f64', 'ts_sig_a_f32', 'ts_sig_a_i32', 'ts_sig_a_u16', ...
    'ts_sig_a_i8',  'ts_sig_a_log', ...
    'ts_sig_b_f32', 'ts_sig_b_i32', ...
    'ts_sig_c_f64', 'ts_sig_c_f32', '-v7', '-nocompression');
fprintf('[OK] flat timeseries v7 file written\n');

% v7.3: write as plain structs (Time + Data fields) so that Mat73Interface
% can read them directly without an MCOS timeseries deserialiser.
ts_sig_a_f64 = struct('Time', t10,  'Data', sig_a_f64);
ts_sig_a_f32 = struct('Time', t10,  'Data', sig_a_f32);
ts_sig_a_i32 = struct('Time', t10,  'Data', sig_a_i32);
ts_sig_a_u16 = struct('Time', t10,  'Data', sig_a_u16);
ts_sig_a_i8  = struct('Time', t10,  'Data', sig_a_i8);
ts_sig_a_log = struct('Time', t10,  'Data', sig_a_log);
ts_sig_b_f32 = struct('Time', t10,  'Data', sig_b_f32);
ts_sig_b_i32 = struct('Time', t10,  'Data', sig_b_i32);
ts_sig_c_f64 = struct('Time', t20,  'Data', sig_c_f64);
ts_sig_c_f32 = struct('Time', t20,  'Data', sig_c_f32);

save(fullfile(out_dir, 'mat_v73_flat_timeseries.mat'), ...
    'ts_sig_a_f64', 'ts_sig_a_f32', 'ts_sig_a_i32', 'ts_sig_a_u16', ...
    'ts_sig_a_i8',  'ts_sig_a_log', ...
    'ts_sig_b_f32', 'ts_sig_b_i32', ...
    'ts_sig_c_f64', 'ts_sig_c_f32', '-v7.3');
fprintf('[OK] flat timeseries v7.3 file written (struct layout)\n');

clearvars ts_sig_a_f64 ts_sig_a_f32 ts_sig_a_i32 ts_sig_a_u16 ...
    ts_sig_a_i8 ts_sig_a_log ts_sig_b_f32 ts_sig_b_i32 ...
    ts_sig_c_f64 ts_sig_c_f32

%% =======================================================================
%  4.  STRUCT OF TIMESERIES
%      signals.<name>  one field per dtype / sample rate
% =======================================================================
signals.sig_a_f64 = struct('Time', t10, 'Data', sig_a_f64);
signals.sig_a_f32 = struct('Time', t10, 'Data', sig_a_f32);
signals.sig_a_i32 = struct('Time', t10, 'Data', sig_a_i32);
signals.sig_a_u16 = struct('Time', t10, 'Data', sig_a_u16);
signals.sig_a_i8  = struct('Time', t10, 'Data', sig_a_i8);
signals.sig_a_log = struct('Time', t10, 'Data', sig_a_log);
signals.sig_b_f32 = struct('Time', t10, 'Data', sig_b_f32);
signals.sig_b_i32 = struct('Time', t10, 'Data', sig_b_i32);
signals.sig_c_f64 = struct('Time', t20, 'Data', sig_c_f64);
signals.sig_c_f32 = struct('Time', t20, 'Data', sig_c_f32); %#ok<STRNU>

save(fullfile(out_dir, 'mat_v7_struct_timeseries.mat'),  'signals', '-v7');
fprintf('[OK] struct timeseries v7 file written\n');

% v7.3: replace timeseries objects with plain Time/Data structs
signals.sig_a_f64 = struct('Time', t10, 'Data', sig_a_f64);
signals.sig_a_f32 = struct('Time', t10, 'Data', sig_a_f32);
signals.sig_a_i32 = struct('Time', t10, 'Data', sig_a_i32);
signals.sig_a_u16 = struct('Time', t10, 'Data', sig_a_u16);
signals.sig_a_i8  = struct('Time', t10, 'Data', sig_a_i8);
signals.sig_a_log = struct('Time', t10, 'Data', sig_a_log);
signals.sig_b_f32 = struct('Time', t10, 'Data', sig_b_f32);
signals.sig_b_i32 = struct('Time', t10, 'Data', sig_b_i32);
signals.sig_c_f64 = struct('Time', t20, 'Data', sig_c_f64);
signals.sig_c_f32 = struct('Time', t20, 'Data', sig_c_f32); %#ok<STRNU>

save(fullfile(out_dir, 'mat_v73_struct_timeseries.mat'), 'signals', '-v7.3');
fprintf('[OK] struct timeseries v7.3 file written (struct layout)\n');

clearvars signals

%% -----------------------------------------------------------------------
fprintf('\nAll reference MAT files written to:\n  %s\n', out_dir);

