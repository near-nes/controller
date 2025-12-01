
/**
 *  state_neuron.h
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  Generated from NESTML 8.2.0 at time: 2025-11-30 15:35:07.938415
**/
#ifndef STATE_NEURON
#define STATE_NEURON

#ifndef HAVE_LIBLTDL
#error "NEST was compiled without support for dynamic loading. Please install libltdl and recompile NEST."
#endif

// C++ includes:
#include <cmath>

#include "config.h"

// Includes for random number generator
#include <random>

// Includes from nestkernel:
#include "archiving_node.h"
#include "connection.h"
#include "dict_util.h"
#include "event.h"
#include "nest_types.h"
#include "ring_buffer.h"
#include "universal_data_logger.h"

// Includes from sli:
#include "dictdatum.h"

// uncomment the next line to enable printing of detailed debug information
// #define DEBUG

namespace nest
{
namespace state_neuron_names
{
    const Name _in_rate( "in_rate" );
    const Name _out_rate( "out_rate" );
    const Name _spike_count_out( "spike_count_out" );
    const Name _current_fbk_input( "current_fbk_input" );
    const Name _current_pred_input( "current_pred_input" );
    const Name _fbk_buffer( "fbk_buffer" );
    const Name _pred_buffer( "pred_buffer" );
    const Name _fbk_counts( "fbk_counts" );
    const Name _pred_counts( "pred_counts" );
    const Name _tick( "tick" );
    const Name _position_count( "position_count" );
    const Name _mean_fbk( "mean_fbk" );
    const Name _mean_pred( "mean_pred" );
    const Name _var_fbk( "var_fbk" );
    const Name _var_pred( "var_pred" );
    const Name _CV_fbk( "CV_fbk" );
    const Name _CV_pred( "CV_pred" );
    const Name _current_error_input( "current_error_input" );
    const Name _error_buffer( "error_buffer" );
    const Name _err_pos_count( "err_pos_count" );
    const Name _error_counts( "error_counts" );
    const Name _error_rate( "error_rate" );
    const Name _fbk_rate( "fbk_rate" );
    const Name _w_fbk( "w_fbk" );
    const Name _w_pred( "w_pred" );
    const Name _total_CV( "total_CV" );
    const Name _lambda_poisson( "lambda_poisson" );
    const Name _kp( "kp" );
    const Name _pos( "pos" );
    const Name _base_rate( "base_rate" );
    const Name _buffer_size( "buffer_size" );
    const Name _buffer_size_error( "buffer_size_error" );
    const Name _simulation_steps( "simulation_steps" );
    const Name _N_fbk( "N_fbk" );
    const Name _N_pred( "N_pred" );
    const Name _N_error( "N_error" );
    const Name _C_error( "C_error" );
    const Name _fbk_bf_size( "fbk_bf_size" );
    const Name _pred_bf_size( "pred_bf_size" );
    const Name _error_bf_size( "error_bf_size" );
    const Name _time_wait( "time_wait" );
    const Name _time_trial( "time_trial" );

    const Name gsl_abs_error_tol("gsl_abs_error_tol");
    const Name gsl_rel_error_tol("gsl_rel_error_tol");
}
}




#include "nest_time.h"
  typedef size_t nest_port_t;
  typedef size_t nest_rport_t;

/* BeginDocumentation
  Name: state_neuron

  Description:

    

  Parameters:
  The following parameters can be set in the status dictionary.
kp [real]  Gain
pos [boolean]  Sign sensitivity of the neuron
base_rate [Hz]  Base firing rate
buffer_size [ms]  Size of the sliding window
simulation_steps [integer]  Number of simulation steps (simulation_time/resolution())
N_fbk [integer]  Population size for sensory feedback
N_pred [integer]  Population size for sensory prediction


  Dynamic state variables:
in_rate [Hz]  Input firing rate: to be computed from spikes
out_rate [Hz]  Output firing rate: defined accordingly to the input firing rate
spike_count_out [integer]  Outgoing spikes
fbk_buffer [real]  Buffer for sensory feedback spikes
pred_buffer [real]  Buffer for sensory prediction spikes
fbk_counts [real]  Counts of incoming feedback spikes
pred_counts [real]  Counts of incoming prediction spikes
tick [integer]  Tick 
mean_fbk [real]  Mean sensory feedback
mean_pred [real]  Mean sensory prediction
var_fbk [real]  Variance of sensory feedback
var_pred [real]  Variance of sensory prediction
CV_fbk [real]  Coefficient of variation of sensory feedback
CV_pred [real]  Coefficient of variation of sensory prediction
current_error_input [real] ################
lambda_poisson [real]  Parameter of the Poisson distribution defining generator behavior


  Sends: nest::SpikeEvent

  Receives: Spike,  DataLoggingRequest
*/

// Register the neuron model
void register_state_neuron( const std::string& name );

class state_neuron : public nest::ArchivingNode
{
public:
  /**
   * The constructor is only used to create the model prototype in the model manager.
  **/
  state_neuron();

  /**
   * The copy constructor is used to create model copies and instances of the model.
   * @node The copy constructor needs to initialize the parameters and the state.
   *       Initialization of buffers and interal variables is deferred to
   *       @c init_buffers_() and @c pre_run_hook() (or calibrate() in NEST 3.3 and older).
  **/
  state_neuron(const state_neuron &);

  /**
   * Destructor.
  **/
  ~state_neuron() override;

  // -------------------------------------------------------------------------
  //   Import sets of overloaded virtual functions.
  //   See: Technical Issues / Virtual Functions: Overriding, Overloading,
  //        and Hiding
  // -------------------------------------------------------------------------

  using nest::Node::handles_test_event;
  using nest::Node::handle;

  /**
   * Used to validate that we can send nest::SpikeEvent to desired target:port.
  **/
  nest_port_t send_test_event(nest::Node& target, nest_rport_t receptor_type, nest::synindex, bool) override;


  // -------------------------------------------------------------------------
  //   Functions handling incoming events.
  //   We tell nest that we can handle incoming events of various types by
  //   defining handle() for the given event.
  // -------------------------------------------------------------------------


  void handle(nest::SpikeEvent &) override;        //! accept spikes

  void handle(nest::DataLoggingRequest &) override;//! allow recording with multimeter
  nest_port_t handles_test_event(nest::SpikeEvent&, nest_port_t) override;
  nest_port_t handles_test_event(nest::DataLoggingRequest&, nest_port_t) override;

  // -------------------------------------------------------------------------
  //   Functions for getting/setting parameters and state values.
  // -------------------------------------------------------------------------

  void get_status(DictionaryDatum &) const override;
  void set_status(const DictionaryDatum &) override;


  // -------------------------------------------------------------------------
  //   Getters/setters for state block
  // -------------------------------------------------------------------------

  inline double get_in_rate() const
  {
    return S_.in_rate;
  }

  inline void set_in_rate(const double __v)
  {
    S_.in_rate = __v;
  }

  inline double get_out_rate() const
  {
    return S_.out_rate;
  }

  inline void set_out_rate(const double __v)
  {
    S_.out_rate = __v;
  }

  inline long get_spike_count_out() const
  {
    return S_.spike_count_out;
  }

  inline void set_spike_count_out(const long __v)
  {
    S_.spike_count_out = __v;
  }

  inline std::vector< double >  get_current_fbk_input() const
  {
    return S_.current_fbk_input;
  }

  inline void set_current_fbk_input(const std::vector< double >  __v)
  {
    S_.current_fbk_input = __v;
  }

  inline std::vector< double >  get_current_pred_input() const
  {
    return S_.current_pred_input;
  }

  inline void set_current_pred_input(const std::vector< double >  __v)
  {
    S_.current_pred_input = __v;
  }

  inline std::vector< double >  get_fbk_buffer() const
  {
    return S_.fbk_buffer;
  }

  inline void set_fbk_buffer(const std::vector< double >  __v)
  {
    S_.fbk_buffer = __v;
  }

  inline std::vector< double >  get_pred_buffer() const
  {
    return S_.pred_buffer;
  }

  inline void set_pred_buffer(const std::vector< double >  __v)
  {
    S_.pred_buffer = __v;
  }

  inline std::vector< double >  get_fbk_counts() const
  {
    return S_.fbk_counts;
  }

  inline void set_fbk_counts(const std::vector< double >  __v)
  {
    S_.fbk_counts = __v;
  }

  inline std::vector< double >  get_pred_counts() const
  {
    return S_.pred_counts;
  }

  inline void set_pred_counts(const std::vector< double >  __v)
  {
    S_.pred_counts = __v;
  }

  inline long get_tick() const
  {
    return S_.tick;
  }

  inline void set_tick(const long __v)
  {
    S_.tick = __v;
  }

  inline long get_position_count() const
  {
    return S_.position_count;
  }

  inline void set_position_count(const long __v)
  {
    S_.position_count = __v;
  }

  inline double get_mean_fbk() const
  {
    return S_.mean_fbk;
  }

  inline void set_mean_fbk(const double __v)
  {
    S_.mean_fbk = __v;
  }

  inline double get_mean_pred() const
  {
    return S_.mean_pred;
  }

  inline void set_mean_pred(const double __v)
  {
    S_.mean_pred = __v;
  }

  inline double get_var_fbk() const
  {
    return S_.var_fbk;
  }

  inline void set_var_fbk(const double __v)
  {
    S_.var_fbk = __v;
  }

  inline double get_var_pred() const
  {
    return S_.var_pred;
  }

  inline void set_var_pred(const double __v)
  {
    S_.var_pred = __v;
  }

  inline double get_CV_fbk() const
  {
    return S_.CV_fbk;
  }

  inline void set_CV_fbk(const double __v)
  {
    S_.CV_fbk = __v;
  }

  inline double get_CV_pred() const
  {
    return S_.CV_pred;
  }

  inline void set_CV_pred(const double __v)
  {
    S_.CV_pred = __v;
  }

  inline double get_current_error_input() const
  {
    return S_.current_error_input;
  }

  inline void set_current_error_input(const double __v)
  {
    S_.current_error_input = __v;
  }

  inline std::vector< double >  get_error_buffer() const
  {
    return S_.error_buffer;
  }

  inline void set_error_buffer(const std::vector< double >  __v)
  {
    S_.error_buffer = __v;
  }

  inline long get_err_pos_count() const
  {
    return S_.err_pos_count;
  }

  inline void set_err_pos_count(const long __v)
  {
    S_.err_pos_count = __v;
  }

  inline double get_error_counts() const
  {
    return S_.error_counts;
  }

  inline void set_error_counts(const double __v)
  {
    S_.error_counts = __v;
  }

  inline double get_error_rate() const
  {
    return S_.error_rate;
  }

  inline void set_error_rate(const double __v)
  {
    S_.error_rate = __v;
  }

  inline double get_fbk_rate() const
  {
    return S_.fbk_rate;
  }

  inline void set_fbk_rate(const double __v)
  {
    S_.fbk_rate = __v;
  }

  inline double get_w_fbk() const
  {
    return S_.w_fbk;
  }

  inline void set_w_fbk(const double __v)
  {
    S_.w_fbk = __v;
  }

  inline double get_w_pred() const
  {
    return S_.w_pred;
  }

  inline void set_w_pred(const double __v)
  {
    S_.w_pred = __v;
  }

  inline double get_total_CV() const
  {
    return S_.total_CV;
  }

  inline void set_total_CV(const double __v)
  {
    S_.total_CV = __v;
  }

  inline double get_lambda_poisson() const
  {
    return S_.lambda_poisson;
  }

  inline void set_lambda_poisson(const double __v)
  {
    S_.lambda_poisson = __v;
  }


  // -------------------------------------------------------------------------
  //   Getters/setters for parameters
  // -------------------------------------------------------------------------

  inline double get_kp() const
  {
    return P_.kp;
  }

  inline void set_kp(const double __v)
  {
    P_.kp = __v;
  }

  inline bool get_pos() const
  {
    return P_.pos;
  }

  inline void set_pos(const bool __v)
  {
    P_.pos = __v;
  }

  inline double get_base_rate() const
  {
    return P_.base_rate;
  }

  inline void set_base_rate(const double __v)
  {
    P_.base_rate = __v;
  }

  inline double get_buffer_size() const
  {
    return P_.buffer_size;
  }

  inline void set_buffer_size(const double __v)
  {
    P_.buffer_size = __v;
  }

  inline double get_buffer_size_error() const
  {
    return P_.buffer_size_error;
  }

  inline void set_buffer_size_error(const double __v)
  {
    P_.buffer_size_error = __v;
  }

  inline long get_simulation_steps() const
  {
    return P_.simulation_steps;
  }

  inline void set_simulation_steps(const long __v)
  {
    P_.simulation_steps = __v;
  }

  inline long get_N_fbk() const
  {
    return P_.N_fbk;
  }

  inline void set_N_fbk(const long __v)
  {
    P_.N_fbk = __v;
  }

  inline long get_N_pred() const
  {
    return P_.N_pred;
  }

  inline void set_N_pred(const long __v)
  {
    P_.N_pred = __v;
  }

  inline long get_N_error() const
  {
    return P_.N_error;
  }

  inline void set_N_error(const long __v)
  {
    P_.N_error = __v;
  }

  inline double get_C_error() const
  {
    return P_.C_error;
  }

  inline void set_C_error(const double __v)
  {
    P_.C_error = __v;
  }

  inline long get_fbk_bf_size() const
  {
    return P_.fbk_bf_size;
  }

  inline void set_fbk_bf_size(const long __v)
  {
    P_.fbk_bf_size = __v;
  }

  inline long get_pred_bf_size() const
  {
    return P_.pred_bf_size;
  }

  inline void set_pred_bf_size(const long __v)
  {
    P_.pred_bf_size = __v;
  }

  inline long get_error_bf_size() const
  {
    return P_.error_bf_size;
  }

  inline void set_error_bf_size(const long __v)
  {
    P_.error_bf_size = __v;
  }

  inline double get_time_wait() const
  {
    return P_.time_wait;
  }

  inline void set_time_wait(const double __v)
  {
    P_.time_wait = __v;
  }

  inline double get_time_trial() const
  {
    return P_.time_trial;
  }

  inline void set_time_trial(const double __v)
  {
    P_.time_trial = __v;
  }


  // -------------------------------------------------------------------------
  //   Getters/setters for internals
  // -------------------------------------------------------------------------

  inline double get_res() const
  {
    return V_.res;
  }

  inline void set_res(const double __v)
  {
    V_.res = __v;
  }
  inline double get___h() const
  {
    return V_.__h;
  }

  inline void set___h(const double __v)
  {
    V_.__h = __v;
  }
  inline long get_buffer_steps() const
  {
    return V_.buffer_steps;
  }

  inline void set_buffer_steps(const long __v)
  {
    V_.buffer_steps = __v;
  }
  inline long get_trial_steps() const
  {
    return V_.trial_steps;
  }

  inline void set_trial_steps(const long __v)
  {
    V_.trial_steps = __v;
  }
  inline long get_wait_steps() const
  {
    return V_.wait_steps;
  }

  inline void set_wait_steps(const long __v)
  {
    V_.wait_steps = __v;
  }
  inline long get_buffer_error_steps() const
  {
    return V_.buffer_error_steps;
  }

  inline void set_buffer_error_steps(const long __v)
  {
    V_.buffer_error_steps = __v;
  }


  // -------------------------------------------------------------------------
  //   Methods corresponding to event handlers
  // -------------------------------------------------------------------------

  

  // -------------------------------------------------------------------------
  //   Initialization functions
  // -------------------------------------------------------------------------
  void calibrate_time( const nest::TimeConverter& tc ) override;

protected:

private:
  void recompute_internal_variables(bool exclude_timestep=false);

private:
/**
   * Synapse types to connect to
   * @note Excluded lower and upper bounds are defined as MIN_, MAX_.
   *       Excluding port 0 avoids accidental connections.
  **/
  static const nest_port_t MIN_SPIKE_RECEPTOR = 1;
  static const nest_port_t PORT_NOT_AVAILABLE = -1;

  enum SynapseTypes
  {
    FBK_SPIKES_0 = 1,
    FBK_SPIKES_1 = 2,
    FBK_SPIKES_2 = 3,
    FBK_SPIKES_3 = 4,
    FBK_SPIKES_4 = 5,
    FBK_SPIKES_5 = 6,
    FBK_SPIKES_6 = 7,
    FBK_SPIKES_7 = 8,
    FBK_SPIKES_8 = 9,
    FBK_SPIKES_9 = 10,
    FBK_SPIKES_10 = 11,
    FBK_SPIKES_11 = 12,
    FBK_SPIKES_12 = 13,
    FBK_SPIKES_13 = 14,
    FBK_SPIKES_14 = 15,
    FBK_SPIKES_15 = 16,
    FBK_SPIKES_16 = 17,
    FBK_SPIKES_17 = 18,
    FBK_SPIKES_18 = 19,
    FBK_SPIKES_19 = 20,
    FBK_SPIKES_20 = 21,
    FBK_SPIKES_21 = 22,
    FBK_SPIKES_22 = 23,
    FBK_SPIKES_23 = 24,
    FBK_SPIKES_24 = 25,
    FBK_SPIKES_25 = 26,
    FBK_SPIKES_26 = 27,
    FBK_SPIKES_27 = 28,
    FBK_SPIKES_28 = 29,
    FBK_SPIKES_29 = 30,
    FBK_SPIKES_30 = 31,
    FBK_SPIKES_31 = 32,
    FBK_SPIKES_32 = 33,
    FBK_SPIKES_33 = 34,
    FBK_SPIKES_34 = 35,
    FBK_SPIKES_35 = 36,
    FBK_SPIKES_36 = 37,
    FBK_SPIKES_37 = 38,
    FBK_SPIKES_38 = 39,
    FBK_SPIKES_39 = 40,
    FBK_SPIKES_40 = 41,
    FBK_SPIKES_41 = 42,
    FBK_SPIKES_42 = 43,
    FBK_SPIKES_43 = 44,
    FBK_SPIKES_44 = 45,
    FBK_SPIKES_45 = 46,
    FBK_SPIKES_46 = 47,
    FBK_SPIKES_47 = 48,
    FBK_SPIKES_48 = 49,
    FBK_SPIKES_49 = 50,
    FBK_SPIKES_50 = 51,
    FBK_SPIKES_51 = 52,
    FBK_SPIKES_52 = 53,
    FBK_SPIKES_53 = 54,
    FBK_SPIKES_54 = 55,
    FBK_SPIKES_55 = 56,
    FBK_SPIKES_56 = 57,
    FBK_SPIKES_57 = 58,
    FBK_SPIKES_58 = 59,
    FBK_SPIKES_59 = 60,
    FBK_SPIKES_60 = 61,
    FBK_SPIKES_61 = 62,
    FBK_SPIKES_62 = 63,
    FBK_SPIKES_63 = 64,
    FBK_SPIKES_64 = 65,
    FBK_SPIKES_65 = 66,
    FBK_SPIKES_66 = 67,
    FBK_SPIKES_67 = 68,
    FBK_SPIKES_68 = 69,
    FBK_SPIKES_69 = 70,
    FBK_SPIKES_70 = 71,
    FBK_SPIKES_71 = 72,
    FBK_SPIKES_72 = 73,
    FBK_SPIKES_73 = 74,
    FBK_SPIKES_74 = 75,
    FBK_SPIKES_75 = 76,
    FBK_SPIKES_76 = 77,
    FBK_SPIKES_77 = 78,
    FBK_SPIKES_78 = 79,
    FBK_SPIKES_79 = 80,
    FBK_SPIKES_80 = 81,
    FBK_SPIKES_81 = 82,
    FBK_SPIKES_82 = 83,
    FBK_SPIKES_83 = 84,
    FBK_SPIKES_84 = 85,
    FBK_SPIKES_85 = 86,
    FBK_SPIKES_86 = 87,
    FBK_SPIKES_87 = 88,
    FBK_SPIKES_88 = 89,
    FBK_SPIKES_89 = 90,
    FBK_SPIKES_90 = 91,
    FBK_SPIKES_91 = 92,
    FBK_SPIKES_92 = 93,
    FBK_SPIKES_93 = 94,
    FBK_SPIKES_94 = 95,
    FBK_SPIKES_95 = 96,
    FBK_SPIKES_96 = 97,
    FBK_SPIKES_97 = 98,
    FBK_SPIKES_98 = 99,
    FBK_SPIKES_99 = 100,
    FBK_SPIKES_100 = 101,
    FBK_SPIKES_101 = 102,
    FBK_SPIKES_102 = 103,
    FBK_SPIKES_103 = 104,
    FBK_SPIKES_104 = 105,
    FBK_SPIKES_105 = 106,
    FBK_SPIKES_106 = 107,
    FBK_SPIKES_107 = 108,
    FBK_SPIKES_108 = 109,
    FBK_SPIKES_109 = 110,
    FBK_SPIKES_110 = 111,
    FBK_SPIKES_111 = 112,
    FBK_SPIKES_112 = 113,
    FBK_SPIKES_113 = 114,
    FBK_SPIKES_114 = 115,
    FBK_SPIKES_115 = 116,
    FBK_SPIKES_116 = 117,
    FBK_SPIKES_117 = 118,
    FBK_SPIKES_118 = 119,
    FBK_SPIKES_119 = 120,
    FBK_SPIKES_120 = 121,
    FBK_SPIKES_121 = 122,
    FBK_SPIKES_122 = 123,
    FBK_SPIKES_123 = 124,
    FBK_SPIKES_124 = 125,
    FBK_SPIKES_125 = 126,
    FBK_SPIKES_126 = 127,
    FBK_SPIKES_127 = 128,
    FBK_SPIKES_128 = 129,
    FBK_SPIKES_129 = 130,
    FBK_SPIKES_130 = 131,
    FBK_SPIKES_131 = 132,
    FBK_SPIKES_132 = 133,
    FBK_SPIKES_133 = 134,
    FBK_SPIKES_134 = 135,
    FBK_SPIKES_135 = 136,
    FBK_SPIKES_136 = 137,
    FBK_SPIKES_137 = 138,
    FBK_SPIKES_138 = 139,
    FBK_SPIKES_139 = 140,
    FBK_SPIKES_140 = 141,
    FBK_SPIKES_141 = 142,
    FBK_SPIKES_142 = 143,
    FBK_SPIKES_143 = 144,
    FBK_SPIKES_144 = 145,
    FBK_SPIKES_145 = 146,
    FBK_SPIKES_146 = 147,
    FBK_SPIKES_147 = 148,
    FBK_SPIKES_148 = 149,
    FBK_SPIKES_149 = 150,
    FBK_SPIKES_150 = 151,
    FBK_SPIKES_151 = 152,
    FBK_SPIKES_152 = 153,
    FBK_SPIKES_153 = 154,
    FBK_SPIKES_154 = 155,
    FBK_SPIKES_155 = 156,
    FBK_SPIKES_156 = 157,
    FBK_SPIKES_157 = 158,
    FBK_SPIKES_158 = 159,
    FBK_SPIKES_159 = 160,
    FBK_SPIKES_160 = 161,
    FBK_SPIKES_161 = 162,
    FBK_SPIKES_162 = 163,
    FBK_SPIKES_163 = 164,
    FBK_SPIKES_164 = 165,
    FBK_SPIKES_165 = 166,
    FBK_SPIKES_166 = 167,
    FBK_SPIKES_167 = 168,
    FBK_SPIKES_168 = 169,
    FBK_SPIKES_169 = 170,
    FBK_SPIKES_170 = 171,
    FBK_SPIKES_171 = 172,
    FBK_SPIKES_172 = 173,
    FBK_SPIKES_173 = 174,
    FBK_SPIKES_174 = 175,
    FBK_SPIKES_175 = 176,
    FBK_SPIKES_176 = 177,
    FBK_SPIKES_177 = 178,
    FBK_SPIKES_178 = 179,
    FBK_SPIKES_179 = 180,
    FBK_SPIKES_180 = 181,
    FBK_SPIKES_181 = 182,
    FBK_SPIKES_182 = 183,
    FBK_SPIKES_183 = 184,
    FBK_SPIKES_184 = 185,
    FBK_SPIKES_185 = 186,
    FBK_SPIKES_186 = 187,
    FBK_SPIKES_187 = 188,
    FBK_SPIKES_188 = 189,
    FBK_SPIKES_189 = 190,
    FBK_SPIKES_190 = 191,
    FBK_SPIKES_191 = 192,
    FBK_SPIKES_192 = 193,
    FBK_SPIKES_193 = 194,
    FBK_SPIKES_194 = 195,
    FBK_SPIKES_195 = 196,
    FBK_SPIKES_196 = 197,
    FBK_SPIKES_197 = 198,
    FBK_SPIKES_198 = 199,
    FBK_SPIKES_199 = 200,
    PRED_SPIKES_0 = 201,
    PRED_SPIKES_1 = 202,
    PRED_SPIKES_2 = 203,
    PRED_SPIKES_3 = 204,
    PRED_SPIKES_4 = 205,
    PRED_SPIKES_5 = 206,
    PRED_SPIKES_6 = 207,
    PRED_SPIKES_7 = 208,
    PRED_SPIKES_8 = 209,
    PRED_SPIKES_9 = 210,
    PRED_SPIKES_10 = 211,
    PRED_SPIKES_11 = 212,
    PRED_SPIKES_12 = 213,
    PRED_SPIKES_13 = 214,
    PRED_SPIKES_14 = 215,
    PRED_SPIKES_15 = 216,
    PRED_SPIKES_16 = 217,
    PRED_SPIKES_17 = 218,
    PRED_SPIKES_18 = 219,
    PRED_SPIKES_19 = 220,
    PRED_SPIKES_20 = 221,
    PRED_SPIKES_21 = 222,
    PRED_SPIKES_22 = 223,
    PRED_SPIKES_23 = 224,
    PRED_SPIKES_24 = 225,
    PRED_SPIKES_25 = 226,
    PRED_SPIKES_26 = 227,
    PRED_SPIKES_27 = 228,
    PRED_SPIKES_28 = 229,
    PRED_SPIKES_29 = 230,
    PRED_SPIKES_30 = 231,
    PRED_SPIKES_31 = 232,
    PRED_SPIKES_32 = 233,
    PRED_SPIKES_33 = 234,
    PRED_SPIKES_34 = 235,
    PRED_SPIKES_35 = 236,
    PRED_SPIKES_36 = 237,
    PRED_SPIKES_37 = 238,
    PRED_SPIKES_38 = 239,
    PRED_SPIKES_39 = 240,
    PRED_SPIKES_40 = 241,
    PRED_SPIKES_41 = 242,
    PRED_SPIKES_42 = 243,
    PRED_SPIKES_43 = 244,
    PRED_SPIKES_44 = 245,
    PRED_SPIKES_45 = 246,
    PRED_SPIKES_46 = 247,
    PRED_SPIKES_47 = 248,
    PRED_SPIKES_48 = 249,
    PRED_SPIKES_49 = 250,
    PRED_SPIKES_50 = 251,
    PRED_SPIKES_51 = 252,
    PRED_SPIKES_52 = 253,
    PRED_SPIKES_53 = 254,
    PRED_SPIKES_54 = 255,
    PRED_SPIKES_55 = 256,
    PRED_SPIKES_56 = 257,
    PRED_SPIKES_57 = 258,
    PRED_SPIKES_58 = 259,
    PRED_SPIKES_59 = 260,
    PRED_SPIKES_60 = 261,
    PRED_SPIKES_61 = 262,
    PRED_SPIKES_62 = 263,
    PRED_SPIKES_63 = 264,
    PRED_SPIKES_64 = 265,
    PRED_SPIKES_65 = 266,
    PRED_SPIKES_66 = 267,
    PRED_SPIKES_67 = 268,
    PRED_SPIKES_68 = 269,
    PRED_SPIKES_69 = 270,
    PRED_SPIKES_70 = 271,
    PRED_SPIKES_71 = 272,
    PRED_SPIKES_72 = 273,
    PRED_SPIKES_73 = 274,
    PRED_SPIKES_74 = 275,
    PRED_SPIKES_75 = 276,
    PRED_SPIKES_76 = 277,
    PRED_SPIKES_77 = 278,
    PRED_SPIKES_78 = 279,
    PRED_SPIKES_79 = 280,
    PRED_SPIKES_80 = 281,
    PRED_SPIKES_81 = 282,
    PRED_SPIKES_82 = 283,
    PRED_SPIKES_83 = 284,
    PRED_SPIKES_84 = 285,
    PRED_SPIKES_85 = 286,
    PRED_SPIKES_86 = 287,
    PRED_SPIKES_87 = 288,
    PRED_SPIKES_88 = 289,
    PRED_SPIKES_89 = 290,
    PRED_SPIKES_90 = 291,
    PRED_SPIKES_91 = 292,
    PRED_SPIKES_92 = 293,
    PRED_SPIKES_93 = 294,
    PRED_SPIKES_94 = 295,
    PRED_SPIKES_95 = 296,
    PRED_SPIKES_96 = 297,
    PRED_SPIKES_97 = 298,
    PRED_SPIKES_98 = 299,
    PRED_SPIKES_99 = 300,
    PRED_SPIKES_100 = 301,
    PRED_SPIKES_101 = 302,
    PRED_SPIKES_102 = 303,
    PRED_SPIKES_103 = 304,
    PRED_SPIKES_104 = 305,
    PRED_SPIKES_105 = 306,
    PRED_SPIKES_106 = 307,
    PRED_SPIKES_107 = 308,
    PRED_SPIKES_108 = 309,
    PRED_SPIKES_109 = 310,
    PRED_SPIKES_110 = 311,
    PRED_SPIKES_111 = 312,
    PRED_SPIKES_112 = 313,
    PRED_SPIKES_113 = 314,
    PRED_SPIKES_114 = 315,
    PRED_SPIKES_115 = 316,
    PRED_SPIKES_116 = 317,
    PRED_SPIKES_117 = 318,
    PRED_SPIKES_118 = 319,
    PRED_SPIKES_119 = 320,
    PRED_SPIKES_120 = 321,
    PRED_SPIKES_121 = 322,
    PRED_SPIKES_122 = 323,
    PRED_SPIKES_123 = 324,
    PRED_SPIKES_124 = 325,
    PRED_SPIKES_125 = 326,
    PRED_SPIKES_126 = 327,
    PRED_SPIKES_127 = 328,
    PRED_SPIKES_128 = 329,
    PRED_SPIKES_129 = 330,
    PRED_SPIKES_130 = 331,
    PRED_SPIKES_131 = 332,
    PRED_SPIKES_132 = 333,
    PRED_SPIKES_133 = 334,
    PRED_SPIKES_134 = 335,
    PRED_SPIKES_135 = 336,
    PRED_SPIKES_136 = 337,
    PRED_SPIKES_137 = 338,
    PRED_SPIKES_138 = 339,
    PRED_SPIKES_139 = 340,
    PRED_SPIKES_140 = 341,
    PRED_SPIKES_141 = 342,
    PRED_SPIKES_142 = 343,
    PRED_SPIKES_143 = 344,
    PRED_SPIKES_144 = 345,
    PRED_SPIKES_145 = 346,
    PRED_SPIKES_146 = 347,
    PRED_SPIKES_147 = 348,
    PRED_SPIKES_148 = 349,
    PRED_SPIKES_149 = 350,
    PRED_SPIKES_150 = 351,
    PRED_SPIKES_151 = 352,
    PRED_SPIKES_152 = 353,
    PRED_SPIKES_153 = 354,
    PRED_SPIKES_154 = 355,
    PRED_SPIKES_155 = 356,
    PRED_SPIKES_156 = 357,
    PRED_SPIKES_157 = 358,
    PRED_SPIKES_158 = 359,
    PRED_SPIKES_159 = 360,
    PRED_SPIKES_160 = 361,
    PRED_SPIKES_161 = 362,
    PRED_SPIKES_162 = 363,
    PRED_SPIKES_163 = 364,
    PRED_SPIKES_164 = 365,
    PRED_SPIKES_165 = 366,
    PRED_SPIKES_166 = 367,
    PRED_SPIKES_167 = 368,
    PRED_SPIKES_168 = 369,
    PRED_SPIKES_169 = 370,
    PRED_SPIKES_170 = 371,
    PRED_SPIKES_171 = 372,
    PRED_SPIKES_172 = 373,
    PRED_SPIKES_173 = 374,
    PRED_SPIKES_174 = 375,
    PRED_SPIKES_175 = 376,
    PRED_SPIKES_176 = 377,
    PRED_SPIKES_177 = 378,
    PRED_SPIKES_178 = 379,
    PRED_SPIKES_179 = 380,
    PRED_SPIKES_180 = 381,
    PRED_SPIKES_181 = 382,
    PRED_SPIKES_182 = 383,
    PRED_SPIKES_183 = 384,
    PRED_SPIKES_184 = 385,
    PRED_SPIKES_185 = 386,
    PRED_SPIKES_186 = 387,
    PRED_SPIKES_187 = 388,
    PRED_SPIKES_188 = 389,
    PRED_SPIKES_189 = 390,
    PRED_SPIKES_190 = 391,
    PRED_SPIKES_191 = 392,
    PRED_SPIKES_192 = 393,
    PRED_SPIKES_193 = 394,
    PRED_SPIKES_194 = 395,
    PRED_SPIKES_195 = 396,
    PRED_SPIKES_196 = 397,
    PRED_SPIKES_197 = 398,
    PRED_SPIKES_198 = 399,
    PRED_SPIKES_199 = 400,
    ERROR_SPIKES = 401,
    MAX_SPIKE_RECEPTOR = 402
  };

  enum ContinuousInput
  {
    NUM_CONTINUOUS_INPUT_PORTS = 0
  };

  static const size_t NUM_SPIKE_RECEPTORS = MAX_SPIKE_RECEPTOR - MIN_SPIKE_RECEPTOR;

static std::vector< std::tuple< int, int > > rport_to_nestml_buffer_idx;

  /**
   * Reset state of neuron.
  **/

  void init_state_internal_();

  /**
   * Reset internal buffers of neuron.
  **/
  void init_buffers_() override;

  /**
   * Initialize auxiliary quantities, leave parameters and state untouched.
  **/
  void pre_run_hook() override;

  /**
   * Take neuron through given time interval
  **/
  void update(nest::Time const &, const long, const long) override;

  // The next two classes need to be friends to access the State_ class/member
  friend class nest::DynamicRecordablesMap< state_neuron >;
  friend class nest::DynamicUniversalDataLogger< state_neuron >;
  friend class nest::DataAccessFunctor< state_neuron >;

  /**
   * Free parameters of the neuron.
   *


   *
   * These are the parameters that can be set by the user through @c `node.set()`.
   * They are initialized from the model prototype when the node is created.
   * Parameters do not change during calls to @c update() and are not reset by
   * @c ResetNetwork.
   *
   * @note Parameters_ need neither copy constructor nor @c operator=(), since
   *       all its members are copied properly by the default copy constructor
   *       and assignment operator. Important:
   *       - If Parameters_ contained @c Time members, you need to define the
   *         assignment operator to recalibrate all members of type @c Time . You
   *         may also want to define the assignment operator.
   *       - If Parameters_ contained members that cannot copy themselves, such
   *         as C-style arrays, you need to define the copy constructor and
   *         assignment operator to copy those members.
  **/
  struct Parameters_
  {    
    //!  Gain
    double kp;
    //!  Sign sensitivity of the neuron
    bool pos;
    //!  Base firing rate
    double base_rate;
    //!  Size of the sliding window
    double buffer_size;
    double buffer_size_error;
    //!  Number of simulation steps (simulation_time/resolution())
    long simulation_steps;
    //!  Population size for sensory feedback
    long N_fbk;
    //!  Population size for sensory prediction
    long N_pred;
    long N_error;
    double C_error;
    long fbk_bf_size;
    long pred_bf_size;
    long error_bf_size;
    double time_wait;
    double time_trial;

    /**
     * Initialize parameters to their default values.
    **/
    Parameters_();
  };

  /**
   * Dynamic state of the neuron.
   *
   *
   *
   * These are the state variables that are advanced in time by calls to
   * @c update(). In many models, some or all of them can be set by the user
   * through @c `node.set()`. The state variables are initialized from the model
   * prototype when the node is created. State variables are reset by @c ResetNetwork.
   *
   * @note State_ need neither copy constructor nor @c operator=(), since
   *       all its members are copied properly by the default copy constructor
   *       and assignment operator. Important:
   *       - If State_ contained @c Time members, you need to define the
   *         assignment operator to recalibrate all members of type @c Time . You
   *         may also want to define the assignment operator.
   *       - If State_ contained members that cannot copy themselves, such
   *         as C-style arrays, you need to define the copy constructor and
   *         assignment operator to copy those members.
  **/
  struct State_
  {
enum StateVecVars {
    IN_RATE = 0,
    OUT_RATE = 1,
    CURRENT_FBK_INPUT = 2,
    CURRENT_PRED_INPUT = 202,
    FBK_BUFFER = 402,
    PRED_BUFFER = 30402,
    FBK_COUNTS = 60402,
    PRED_COUNTS = 60602,
    MEAN_FBK = 60802,
    MEAN_PRED = 60803,
    VAR_FBK = 60804,
    VAR_PRED = 60805,
    CV_FBK = 60806,
    CV_PRED = 60807,
    CURRENT_ERROR_INPUT = 60808,
    ERROR_BUFFER = 60809,
    ERROR_COUNTS = 60834,
    ERROR_RATE = 60835,
    FBK_RATE = 60836,
    W_FBK = 60837,
    W_PRED = 60838,
    TOTAL_CV = 60839,
    LAMBDA_POISSON = 60840,
};    
    //!  Input firing rate: to be computed from spikes
    double in_rate;
    //!  Output firing rate: defined accordingly to the input firing rate
    double out_rate;
    //!  Outgoing spikes
    long spike_count_out;
    std::vector< double >  current_fbk_input;
    std::vector< double >  current_pred_input;
    //!  Buffer for sensory feedback spikes
    std::vector< double >  fbk_buffer;
    //!  Buffer for sensory prediction spikes
    std::vector< double >  pred_buffer;
    //!  Counts of incoming feedback spikes
    std::vector< double >  fbk_counts;
    //!  Counts of incoming prediction spikes
    std::vector< double >  pred_counts;
    //!  Tick 
    long tick;
    long position_count;
    //!  Mean sensory feedback
    double mean_fbk;
    //!  Mean sensory prediction
    double mean_pred;
    //!  Variance of sensory feedback
    double var_fbk;
    //!  Variance of sensory prediction
    double var_pred;
    //!  Coefficient of variation of sensory feedback
    double CV_fbk;
    //!  Coefficient of variation of sensory prediction
    double CV_pred;
    //! ################
    double current_error_input;
    std::vector< double >  error_buffer;
    long err_pos_count;
    double error_counts;
    double error_rate;
    double fbk_rate;
    double w_fbk;
    double w_pred;
    double total_CV;
    //!  Parameter of the Poisson distribution defining generator behavior
    double lambda_poisson;

    State_();
  };

  struct DelayedVariables_
  {
  };

  /**
   * Internal variables of the neuron.
   *
   *
   *
   * These variables must be initialized by @c pre_run_hook (or calibrate in NEST 3.3 and older), which is called before
   * the first call to @c update() upon each call to @c Simulate.
   * @node Variables_ needs neither constructor, copy constructor or assignment operator,
   *       since it is initialized by @c pre_run_hook() (or calibrate() in NEST 3.3 and older). If Variables_ has members that
   *       cannot destroy themselves, Variables_ will need a destructor.
  **/
  struct Variables_
  {
    double res;
    double __h;
    long buffer_steps;
    long trial_steps;
    long wait_steps;
    long buffer_error_steps;
  };

  /**
   * Buffers of the neuron.
   * Usually buffers for incoming spikes and data logged for analog recorders.
   * Buffers must be initialized by @c init_buffers_(), which is called before
   * @c pre_run_hook() (or calibrate() in NEST 3.3 and older) on the first call to @c Simulate after the start of NEST,
   * ResetKernel or ResetNetwork.
   * @node Buffers_ needs neither constructor, copy constructor or assignment operator,
   *       since it is initialized by @c init_nodes_(). If Buffers_ has members that
   *       cannot destroy themselves, Buffers_ will need a destructor.
  **/
  struct Buffers_
  {
    Buffers_(state_neuron &);
    Buffers_(const Buffers_ &, state_neuron &);

    /**
     * Logger for all analog data
    **/
    nest::DynamicUniversalDataLogger<state_neuron> logger_;

    // -----------------------------------------------------------------------
    //   Spike buffers and sums of incoming spikes/currents per timestep
    // -----------------------------------------------------------------------    



    /**
     * Buffer containing the incoming spikes
    **/
    inline std::vector< nest::RingBuffer >& get_spike_inputs_()
    {
        return spike_inputs_;
    }
    std::vector< nest::RingBuffer > spike_inputs_;

    /**
     * Buffer containing the sum of all the incoming spikes
    **/
    inline std::vector< double >& get_spike_inputs_grid_sum_()
    {
        return spike_inputs_grid_sum_;
    }
    std::vector< double > spike_inputs_grid_sum_;

    /**
     * Buffer containing a flag whether incoming spikes have been received on a given port
    **/
    inline std::vector< nest::RingBuffer >& get_spike_input_received_()
    {
        return spike_input_received_;
    }
    std::vector< nest::RingBuffer > spike_input_received_;

    /**
     * Buffer containing a flag whether incoming spikes have been received on a given port
    **/
    inline std::vector< double >& get_spike_input_received_grid_sum_()
    {
        return spike_input_received_grid_sum_;
    }
    std::vector< double > spike_input_received_grid_sum_;

    // -----------------------------------------------------------------------
    //   Continuous-input buffers
    // -----------------------------------------------------------------------

    




    /**
     * Buffer containing the incoming continuous input
    **/
    inline std::vector< nest::RingBuffer >& get_continuous_inputs_()
    {
        return continuous_inputs_;
    }
    std::vector< nest::RingBuffer > continuous_inputs_;

    /**
     * Buffer containing the sum of all the continuous inputs
    **/
    inline std::vector< double >& get_continuous_inputs_grid_sum_()
    {
        return continuous_inputs_grid_sum_;
    }
    std::vector< double > continuous_inputs_grid_sum_;
  };

  // -------------------------------------------------------------------------
  //   Getters/setters for inline expressions
  // -------------------------------------------------------------------------

  

  // -------------------------------------------------------------------------
  //   Getters/setters for input buffers
  // -------------------------------------------------------------------------  




  /**
   * Buffer containing the incoming spikes
  **/
  inline std::vector< nest::RingBuffer >& get_spike_inputs_()
  {
      return B_.get_spike_inputs_();
  }

  /**
   * Buffer containing the sum of all the incoming spikes
  **/
  inline std::vector< double >& get_spike_inputs_grid_sum_()
  {
      return B_.get_spike_inputs_grid_sum_();
  }

  /**
   * Buffer containing a flag whether incoming spikes have been received on a given port
  **/
  inline std::vector< nest::RingBuffer >& get_spike_input_received_()
  {
      return B_.get_spike_input_received_();
  }

  /**
   * Buffer containing a flag whether incoming spikes have been received on a given port
  **/
  inline std::vector< double >& get_spike_input_received_grid_sum_()
  {
      return B_.get_spike_input_received_grid_sum_();
  }




  /**
   * Buffer containing the incoming continuous input
  **/
  inline std::vector< nest::RingBuffer >& get_continuous_inputs_()
  {
      return B_.get_continuous_inputs_();
  }

  /**
   * Buffer containing the sum of all the continuous inputs
  **/
  inline std::vector< double >& get_continuous_inputs_grid_sum_()
  {
      return B_.get_continuous_inputs_grid_sum_();
  }

  // -------------------------------------------------------------------------
  //   Member variables of neuron model.
  //   Each model neuron should have precisely the following four data members,
  //   which are one instance each of the parameters, state, buffers and variables
  //   structures. Experience indicates that the state and variables member should
  //   be next to each other to achieve good efficiency (caching).
  //   Note: Devices require one additional data member, an instance of the
  //   ``Device`` child class they belong to.
  // -------------------------------------------------------------------------


  Parameters_       P_;        //!< Free parameters.
  State_            S_;        //!< Dynamic state.
  DelayedVariables_ DV_;       //!< Delayed state variables.
  Variables_        V_;        //!< Internal Variables
  Buffers_          B_;        //!< Buffers.

  //! Mapping of recordables names to access functions
  nest::DynamicRecordablesMap<state_neuron> recordablesMap_;
  nest::DataAccessFunctor< state_neuron > get_data_access_functor( size_t elem );
  std::string get_var_name(size_t elem, std::string var_name);
  void insert_recordables(size_t first=0);


inline double get_state_element(size_t elem)
  {
    if
    (elem == State_::IN_RATE)
    {
      return S_.in_rate;
    }
    else if
    (elem == State_::OUT_RATE)
    {
      return S_.out_rate;
    }
    else if(elem >= State_::CURRENT_FBK_INPUT and elem < State_::CURRENT_FBK_INPUT + 
P_.N_fbk)
    {
      return S_.current_fbk_input[ elem - State_::CURRENT_FBK_INPUT ];
    }
    else if(elem >= State_::CURRENT_PRED_INPUT and elem < State_::CURRENT_PRED_INPUT + 
P_.N_pred)
    {
      return S_.current_pred_input[ elem - State_::CURRENT_PRED_INPUT ];
    }
    else if(elem >= State_::FBK_BUFFER and elem < State_::FBK_BUFFER + 
P_.fbk_bf_size)
    {
      return S_.fbk_buffer[ elem - State_::FBK_BUFFER ];
    }
    else if(elem >= State_::PRED_BUFFER and elem < State_::PRED_BUFFER + 
P_.pred_bf_size)
    {
      return S_.pred_buffer[ elem - State_::PRED_BUFFER ];
    }
    else if(elem >= State_::FBK_COUNTS and elem < State_::FBK_COUNTS + 
P_.N_fbk)
    {
      return S_.fbk_counts[ elem - State_::FBK_COUNTS ];
    }
    else if(elem >= State_::PRED_COUNTS and elem < State_::PRED_COUNTS + 
P_.N_pred)
    {
      return S_.pred_counts[ elem - State_::PRED_COUNTS ];
    }
    else if
    (elem == State_::MEAN_FBK)
    {
      return S_.mean_fbk;
    }
    else if
    (elem == State_::MEAN_PRED)
    {
      return S_.mean_pred;
    }
    else if
    (elem == State_::VAR_FBK)
    {
      return S_.var_fbk;
    }
    else if
    (elem == State_::VAR_PRED)
    {
      return S_.var_pred;
    }
    else if
    (elem == State_::CV_FBK)
    {
      return S_.CV_fbk;
    }
    else if
    (elem == State_::CV_PRED)
    {
      return S_.CV_pred;
    }
    else if
    (elem == State_::CURRENT_ERROR_INPUT)
    {
      return S_.current_error_input;
    }
    else if(elem >= State_::ERROR_BUFFER and elem < State_::ERROR_BUFFER + 
P_.error_bf_size)
    {
      return S_.error_buffer[ elem - State_::ERROR_BUFFER ];
    }
    else if
    (elem == State_::ERROR_COUNTS)
    {
      return S_.error_counts;
    }
    else if
    (elem == State_::ERROR_RATE)
    {
      return S_.error_rate;
    }
    else if
    (elem == State_::FBK_RATE)
    {
      return S_.fbk_rate;
    }
    else if
    (elem == State_::W_FBK)
    {
      return S_.w_fbk;
    }
    else if
    (elem == State_::W_PRED)
    {
      return S_.w_pred;
    }
    else if
    (elem == State_::TOTAL_CV)
    {
      return S_.total_CV;
    }
    else
    {
      return S_.lambda_poisson;
    }
  }
  nest::normal_distribution normal_dev_; //!< random deviate generator
  nest::poisson_distribution poisson_dev_; //!< random deviate generator

}; /* neuron state_neuron */

inline nest_port_t state_neuron::send_test_event(nest::Node& target, nest_rport_t receptor_type, nest::synindex, bool)
{
  // You should usually not change the code in this function.
  // It confirms that the target of connection @c c accepts @c nest::SpikeEvent on
  // the given @c receptor_type.
  nest::SpikeEvent e;
  e.set_sender(*this);
  return target.handles_test_event(e, receptor_type);
}

inline nest_port_t state_neuron::handles_test_event(nest::SpikeEvent&, nest_port_t receptor_type)
{
    assert( B_.spike_inputs_.size() == NUM_SPIKE_RECEPTORS );
    if ( receptor_type < MIN_SPIKE_RECEPTOR or receptor_type >= MAX_SPIKE_RECEPTOR )
    {
      throw nest::UnknownReceptorType( receptor_type, get_name() );
    }
    return receptor_type - MIN_SPIKE_RECEPTOR;
}

inline nest_port_t state_neuron::handles_test_event(nest::DataLoggingRequest& dlr, nest_port_t receptor_type)
{
  // You should usually not change the code in this function.
  // It confirms to the connection management system that we are able
  // to handle @c DataLoggingRequest on port 0.
  // The function also tells the built-in UniversalDataLogger that this node
  // is recorded from and that it thus needs to collect data during simulation.
  if (receptor_type != 0)
  {
    throw nest::UnknownReceptorType(receptor_type, get_name());
  }

  return B_.logger_.connect_logging_device(dlr, recordablesMap_);
}

inline void state_neuron::get_status(DictionaryDatum &__d) const
{
  // parameters
  def< double >(__d, nest::state_neuron_names::_kp, get_kp());
  def< bool >(__d, nest::state_neuron_names::_pos, get_pos());
  def< double >(__d, nest::state_neuron_names::_base_rate, get_base_rate());
  def< double >(__d, nest::state_neuron_names::_buffer_size, get_buffer_size());
  def< double >(__d, nest::state_neuron_names::_buffer_size_error, get_buffer_size_error());
  def< long >(__d, nest::state_neuron_names::_simulation_steps, get_simulation_steps());
  def< long >(__d, nest::state_neuron_names::_N_fbk, get_N_fbk());
  def< long >(__d, nest::state_neuron_names::_N_pred, get_N_pred());
  def< long >(__d, nest::state_neuron_names::_N_error, get_N_error());
  def< double >(__d, nest::state_neuron_names::_C_error, get_C_error());
  def< long >(__d, nest::state_neuron_names::_fbk_bf_size, get_fbk_bf_size());
  def< long >(__d, nest::state_neuron_names::_pred_bf_size, get_pred_bf_size());
  def< long >(__d, nest::state_neuron_names::_error_bf_size, get_error_bf_size());
  def< double >(__d, nest::state_neuron_names::_time_wait, get_time_wait());
  def< double >(__d, nest::state_neuron_names::_time_trial, get_time_trial());

  // initial values for state variables in ODE or kernel
  def< double >(__d, nest::state_neuron_names::_in_rate, get_in_rate());
  def< double >(__d, nest::state_neuron_names::_out_rate, get_out_rate());
  def< long >(__d, nest::state_neuron_names::_spike_count_out, get_spike_count_out());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_current_fbk_input, get_current_fbk_input());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_current_pred_input, get_current_pred_input());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_fbk_buffer, get_fbk_buffer());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_pred_buffer, get_pred_buffer());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_fbk_counts, get_fbk_counts());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_pred_counts, get_pred_counts());
  def< long >(__d, nest::state_neuron_names::_tick, get_tick());
  def< long >(__d, nest::state_neuron_names::_position_count, get_position_count());
  def< double >(__d, nest::state_neuron_names::_mean_fbk, get_mean_fbk());
  def< double >(__d, nest::state_neuron_names::_mean_pred, get_mean_pred());
  def< double >(__d, nest::state_neuron_names::_var_fbk, get_var_fbk());
  def< double >(__d, nest::state_neuron_names::_var_pred, get_var_pred());
  def< double >(__d, nest::state_neuron_names::_CV_fbk, get_CV_fbk());
  def< double >(__d, nest::state_neuron_names::_CV_pred, get_CV_pred());
  def< double >(__d, nest::state_neuron_names::_current_error_input, get_current_error_input());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_error_buffer, get_error_buffer());
  def< long >(__d, nest::state_neuron_names::_err_pos_count, get_err_pos_count());
  def< double >(__d, nest::state_neuron_names::_error_counts, get_error_counts());
  def< double >(__d, nest::state_neuron_names::_error_rate, get_error_rate());
  def< double >(__d, nest::state_neuron_names::_fbk_rate, get_fbk_rate());
  def< double >(__d, nest::state_neuron_names::_w_fbk, get_w_fbk());
  def< double >(__d, nest::state_neuron_names::_w_pred, get_w_pred());
  def< double >(__d, nest::state_neuron_names::_total_CV, get_total_CV());
  def< double >(__d, nest::state_neuron_names::_lambda_poisson, get_lambda_poisson());

  ArchivingNode::get_status( __d );
  DictionaryDatum __receptor_type = new Dictionary();
    ( *__receptor_type )[ "FBK_SPIKES_0" ] = 1,
    ( *__receptor_type )[ "FBK_SPIKES_1" ] = 2,
    ( *__receptor_type )[ "FBK_SPIKES_2" ] = 3,
    ( *__receptor_type )[ "FBK_SPIKES_3" ] = 4,
    ( *__receptor_type )[ "FBK_SPIKES_4" ] = 5,
    ( *__receptor_type )[ "FBK_SPIKES_5" ] = 6,
    ( *__receptor_type )[ "FBK_SPIKES_6" ] = 7,
    ( *__receptor_type )[ "FBK_SPIKES_7" ] = 8,
    ( *__receptor_type )[ "FBK_SPIKES_8" ] = 9,
    ( *__receptor_type )[ "FBK_SPIKES_9" ] = 10,
    ( *__receptor_type )[ "FBK_SPIKES_10" ] = 11,
    ( *__receptor_type )[ "FBK_SPIKES_11" ] = 12,
    ( *__receptor_type )[ "FBK_SPIKES_12" ] = 13,
    ( *__receptor_type )[ "FBK_SPIKES_13" ] = 14,
    ( *__receptor_type )[ "FBK_SPIKES_14" ] = 15,
    ( *__receptor_type )[ "FBK_SPIKES_15" ] = 16,
    ( *__receptor_type )[ "FBK_SPIKES_16" ] = 17,
    ( *__receptor_type )[ "FBK_SPIKES_17" ] = 18,
    ( *__receptor_type )[ "FBK_SPIKES_18" ] = 19,
    ( *__receptor_type )[ "FBK_SPIKES_19" ] = 20,
    ( *__receptor_type )[ "FBK_SPIKES_20" ] = 21,
    ( *__receptor_type )[ "FBK_SPIKES_21" ] = 22,
    ( *__receptor_type )[ "FBK_SPIKES_22" ] = 23,
    ( *__receptor_type )[ "FBK_SPIKES_23" ] = 24,
    ( *__receptor_type )[ "FBK_SPIKES_24" ] = 25,
    ( *__receptor_type )[ "FBK_SPIKES_25" ] = 26,
    ( *__receptor_type )[ "FBK_SPIKES_26" ] = 27,
    ( *__receptor_type )[ "FBK_SPIKES_27" ] = 28,
    ( *__receptor_type )[ "FBK_SPIKES_28" ] = 29,
    ( *__receptor_type )[ "FBK_SPIKES_29" ] = 30,
    ( *__receptor_type )[ "FBK_SPIKES_30" ] = 31,
    ( *__receptor_type )[ "FBK_SPIKES_31" ] = 32,
    ( *__receptor_type )[ "FBK_SPIKES_32" ] = 33,
    ( *__receptor_type )[ "FBK_SPIKES_33" ] = 34,
    ( *__receptor_type )[ "FBK_SPIKES_34" ] = 35,
    ( *__receptor_type )[ "FBK_SPIKES_35" ] = 36,
    ( *__receptor_type )[ "FBK_SPIKES_36" ] = 37,
    ( *__receptor_type )[ "FBK_SPIKES_37" ] = 38,
    ( *__receptor_type )[ "FBK_SPIKES_38" ] = 39,
    ( *__receptor_type )[ "FBK_SPIKES_39" ] = 40,
    ( *__receptor_type )[ "FBK_SPIKES_40" ] = 41,
    ( *__receptor_type )[ "FBK_SPIKES_41" ] = 42,
    ( *__receptor_type )[ "FBK_SPIKES_42" ] = 43,
    ( *__receptor_type )[ "FBK_SPIKES_43" ] = 44,
    ( *__receptor_type )[ "FBK_SPIKES_44" ] = 45,
    ( *__receptor_type )[ "FBK_SPIKES_45" ] = 46,
    ( *__receptor_type )[ "FBK_SPIKES_46" ] = 47,
    ( *__receptor_type )[ "FBK_SPIKES_47" ] = 48,
    ( *__receptor_type )[ "FBK_SPIKES_48" ] = 49,
    ( *__receptor_type )[ "FBK_SPIKES_49" ] = 50,
    ( *__receptor_type )[ "FBK_SPIKES_50" ] = 51,
    ( *__receptor_type )[ "FBK_SPIKES_51" ] = 52,
    ( *__receptor_type )[ "FBK_SPIKES_52" ] = 53,
    ( *__receptor_type )[ "FBK_SPIKES_53" ] = 54,
    ( *__receptor_type )[ "FBK_SPIKES_54" ] = 55,
    ( *__receptor_type )[ "FBK_SPIKES_55" ] = 56,
    ( *__receptor_type )[ "FBK_SPIKES_56" ] = 57,
    ( *__receptor_type )[ "FBK_SPIKES_57" ] = 58,
    ( *__receptor_type )[ "FBK_SPIKES_58" ] = 59,
    ( *__receptor_type )[ "FBK_SPIKES_59" ] = 60,
    ( *__receptor_type )[ "FBK_SPIKES_60" ] = 61,
    ( *__receptor_type )[ "FBK_SPIKES_61" ] = 62,
    ( *__receptor_type )[ "FBK_SPIKES_62" ] = 63,
    ( *__receptor_type )[ "FBK_SPIKES_63" ] = 64,
    ( *__receptor_type )[ "FBK_SPIKES_64" ] = 65,
    ( *__receptor_type )[ "FBK_SPIKES_65" ] = 66,
    ( *__receptor_type )[ "FBK_SPIKES_66" ] = 67,
    ( *__receptor_type )[ "FBK_SPIKES_67" ] = 68,
    ( *__receptor_type )[ "FBK_SPIKES_68" ] = 69,
    ( *__receptor_type )[ "FBK_SPIKES_69" ] = 70,
    ( *__receptor_type )[ "FBK_SPIKES_70" ] = 71,
    ( *__receptor_type )[ "FBK_SPIKES_71" ] = 72,
    ( *__receptor_type )[ "FBK_SPIKES_72" ] = 73,
    ( *__receptor_type )[ "FBK_SPIKES_73" ] = 74,
    ( *__receptor_type )[ "FBK_SPIKES_74" ] = 75,
    ( *__receptor_type )[ "FBK_SPIKES_75" ] = 76,
    ( *__receptor_type )[ "FBK_SPIKES_76" ] = 77,
    ( *__receptor_type )[ "FBK_SPIKES_77" ] = 78,
    ( *__receptor_type )[ "FBK_SPIKES_78" ] = 79,
    ( *__receptor_type )[ "FBK_SPIKES_79" ] = 80,
    ( *__receptor_type )[ "FBK_SPIKES_80" ] = 81,
    ( *__receptor_type )[ "FBK_SPIKES_81" ] = 82,
    ( *__receptor_type )[ "FBK_SPIKES_82" ] = 83,
    ( *__receptor_type )[ "FBK_SPIKES_83" ] = 84,
    ( *__receptor_type )[ "FBK_SPIKES_84" ] = 85,
    ( *__receptor_type )[ "FBK_SPIKES_85" ] = 86,
    ( *__receptor_type )[ "FBK_SPIKES_86" ] = 87,
    ( *__receptor_type )[ "FBK_SPIKES_87" ] = 88,
    ( *__receptor_type )[ "FBK_SPIKES_88" ] = 89,
    ( *__receptor_type )[ "FBK_SPIKES_89" ] = 90,
    ( *__receptor_type )[ "FBK_SPIKES_90" ] = 91,
    ( *__receptor_type )[ "FBK_SPIKES_91" ] = 92,
    ( *__receptor_type )[ "FBK_SPIKES_92" ] = 93,
    ( *__receptor_type )[ "FBK_SPIKES_93" ] = 94,
    ( *__receptor_type )[ "FBK_SPIKES_94" ] = 95,
    ( *__receptor_type )[ "FBK_SPIKES_95" ] = 96,
    ( *__receptor_type )[ "FBK_SPIKES_96" ] = 97,
    ( *__receptor_type )[ "FBK_SPIKES_97" ] = 98,
    ( *__receptor_type )[ "FBK_SPIKES_98" ] = 99,
    ( *__receptor_type )[ "FBK_SPIKES_99" ] = 100,
    ( *__receptor_type )[ "FBK_SPIKES_100" ] = 101,
    ( *__receptor_type )[ "FBK_SPIKES_101" ] = 102,
    ( *__receptor_type )[ "FBK_SPIKES_102" ] = 103,
    ( *__receptor_type )[ "FBK_SPIKES_103" ] = 104,
    ( *__receptor_type )[ "FBK_SPIKES_104" ] = 105,
    ( *__receptor_type )[ "FBK_SPIKES_105" ] = 106,
    ( *__receptor_type )[ "FBK_SPIKES_106" ] = 107,
    ( *__receptor_type )[ "FBK_SPIKES_107" ] = 108,
    ( *__receptor_type )[ "FBK_SPIKES_108" ] = 109,
    ( *__receptor_type )[ "FBK_SPIKES_109" ] = 110,
    ( *__receptor_type )[ "FBK_SPIKES_110" ] = 111,
    ( *__receptor_type )[ "FBK_SPIKES_111" ] = 112,
    ( *__receptor_type )[ "FBK_SPIKES_112" ] = 113,
    ( *__receptor_type )[ "FBK_SPIKES_113" ] = 114,
    ( *__receptor_type )[ "FBK_SPIKES_114" ] = 115,
    ( *__receptor_type )[ "FBK_SPIKES_115" ] = 116,
    ( *__receptor_type )[ "FBK_SPIKES_116" ] = 117,
    ( *__receptor_type )[ "FBK_SPIKES_117" ] = 118,
    ( *__receptor_type )[ "FBK_SPIKES_118" ] = 119,
    ( *__receptor_type )[ "FBK_SPIKES_119" ] = 120,
    ( *__receptor_type )[ "FBK_SPIKES_120" ] = 121,
    ( *__receptor_type )[ "FBK_SPIKES_121" ] = 122,
    ( *__receptor_type )[ "FBK_SPIKES_122" ] = 123,
    ( *__receptor_type )[ "FBK_SPIKES_123" ] = 124,
    ( *__receptor_type )[ "FBK_SPIKES_124" ] = 125,
    ( *__receptor_type )[ "FBK_SPIKES_125" ] = 126,
    ( *__receptor_type )[ "FBK_SPIKES_126" ] = 127,
    ( *__receptor_type )[ "FBK_SPIKES_127" ] = 128,
    ( *__receptor_type )[ "FBK_SPIKES_128" ] = 129,
    ( *__receptor_type )[ "FBK_SPIKES_129" ] = 130,
    ( *__receptor_type )[ "FBK_SPIKES_130" ] = 131,
    ( *__receptor_type )[ "FBK_SPIKES_131" ] = 132,
    ( *__receptor_type )[ "FBK_SPIKES_132" ] = 133,
    ( *__receptor_type )[ "FBK_SPIKES_133" ] = 134,
    ( *__receptor_type )[ "FBK_SPIKES_134" ] = 135,
    ( *__receptor_type )[ "FBK_SPIKES_135" ] = 136,
    ( *__receptor_type )[ "FBK_SPIKES_136" ] = 137,
    ( *__receptor_type )[ "FBK_SPIKES_137" ] = 138,
    ( *__receptor_type )[ "FBK_SPIKES_138" ] = 139,
    ( *__receptor_type )[ "FBK_SPIKES_139" ] = 140,
    ( *__receptor_type )[ "FBK_SPIKES_140" ] = 141,
    ( *__receptor_type )[ "FBK_SPIKES_141" ] = 142,
    ( *__receptor_type )[ "FBK_SPIKES_142" ] = 143,
    ( *__receptor_type )[ "FBK_SPIKES_143" ] = 144,
    ( *__receptor_type )[ "FBK_SPIKES_144" ] = 145,
    ( *__receptor_type )[ "FBK_SPIKES_145" ] = 146,
    ( *__receptor_type )[ "FBK_SPIKES_146" ] = 147,
    ( *__receptor_type )[ "FBK_SPIKES_147" ] = 148,
    ( *__receptor_type )[ "FBK_SPIKES_148" ] = 149,
    ( *__receptor_type )[ "FBK_SPIKES_149" ] = 150,
    ( *__receptor_type )[ "FBK_SPIKES_150" ] = 151,
    ( *__receptor_type )[ "FBK_SPIKES_151" ] = 152,
    ( *__receptor_type )[ "FBK_SPIKES_152" ] = 153,
    ( *__receptor_type )[ "FBK_SPIKES_153" ] = 154,
    ( *__receptor_type )[ "FBK_SPIKES_154" ] = 155,
    ( *__receptor_type )[ "FBK_SPIKES_155" ] = 156,
    ( *__receptor_type )[ "FBK_SPIKES_156" ] = 157,
    ( *__receptor_type )[ "FBK_SPIKES_157" ] = 158,
    ( *__receptor_type )[ "FBK_SPIKES_158" ] = 159,
    ( *__receptor_type )[ "FBK_SPIKES_159" ] = 160,
    ( *__receptor_type )[ "FBK_SPIKES_160" ] = 161,
    ( *__receptor_type )[ "FBK_SPIKES_161" ] = 162,
    ( *__receptor_type )[ "FBK_SPIKES_162" ] = 163,
    ( *__receptor_type )[ "FBK_SPIKES_163" ] = 164,
    ( *__receptor_type )[ "FBK_SPIKES_164" ] = 165,
    ( *__receptor_type )[ "FBK_SPIKES_165" ] = 166,
    ( *__receptor_type )[ "FBK_SPIKES_166" ] = 167,
    ( *__receptor_type )[ "FBK_SPIKES_167" ] = 168,
    ( *__receptor_type )[ "FBK_SPIKES_168" ] = 169,
    ( *__receptor_type )[ "FBK_SPIKES_169" ] = 170,
    ( *__receptor_type )[ "FBK_SPIKES_170" ] = 171,
    ( *__receptor_type )[ "FBK_SPIKES_171" ] = 172,
    ( *__receptor_type )[ "FBK_SPIKES_172" ] = 173,
    ( *__receptor_type )[ "FBK_SPIKES_173" ] = 174,
    ( *__receptor_type )[ "FBK_SPIKES_174" ] = 175,
    ( *__receptor_type )[ "FBK_SPIKES_175" ] = 176,
    ( *__receptor_type )[ "FBK_SPIKES_176" ] = 177,
    ( *__receptor_type )[ "FBK_SPIKES_177" ] = 178,
    ( *__receptor_type )[ "FBK_SPIKES_178" ] = 179,
    ( *__receptor_type )[ "FBK_SPIKES_179" ] = 180,
    ( *__receptor_type )[ "FBK_SPIKES_180" ] = 181,
    ( *__receptor_type )[ "FBK_SPIKES_181" ] = 182,
    ( *__receptor_type )[ "FBK_SPIKES_182" ] = 183,
    ( *__receptor_type )[ "FBK_SPIKES_183" ] = 184,
    ( *__receptor_type )[ "FBK_SPIKES_184" ] = 185,
    ( *__receptor_type )[ "FBK_SPIKES_185" ] = 186,
    ( *__receptor_type )[ "FBK_SPIKES_186" ] = 187,
    ( *__receptor_type )[ "FBK_SPIKES_187" ] = 188,
    ( *__receptor_type )[ "FBK_SPIKES_188" ] = 189,
    ( *__receptor_type )[ "FBK_SPIKES_189" ] = 190,
    ( *__receptor_type )[ "FBK_SPIKES_190" ] = 191,
    ( *__receptor_type )[ "FBK_SPIKES_191" ] = 192,
    ( *__receptor_type )[ "FBK_SPIKES_192" ] = 193,
    ( *__receptor_type )[ "FBK_SPIKES_193" ] = 194,
    ( *__receptor_type )[ "FBK_SPIKES_194" ] = 195,
    ( *__receptor_type )[ "FBK_SPIKES_195" ] = 196,
    ( *__receptor_type )[ "FBK_SPIKES_196" ] = 197,
    ( *__receptor_type )[ "FBK_SPIKES_197" ] = 198,
    ( *__receptor_type )[ "FBK_SPIKES_198" ] = 199,
    ( *__receptor_type )[ "FBK_SPIKES_199" ] = 200,
    ( *__receptor_type )[ "PRED_SPIKES_0" ] = 201,
    ( *__receptor_type )[ "PRED_SPIKES_1" ] = 202,
    ( *__receptor_type )[ "PRED_SPIKES_2" ] = 203,
    ( *__receptor_type )[ "PRED_SPIKES_3" ] = 204,
    ( *__receptor_type )[ "PRED_SPIKES_4" ] = 205,
    ( *__receptor_type )[ "PRED_SPIKES_5" ] = 206,
    ( *__receptor_type )[ "PRED_SPIKES_6" ] = 207,
    ( *__receptor_type )[ "PRED_SPIKES_7" ] = 208,
    ( *__receptor_type )[ "PRED_SPIKES_8" ] = 209,
    ( *__receptor_type )[ "PRED_SPIKES_9" ] = 210,
    ( *__receptor_type )[ "PRED_SPIKES_10" ] = 211,
    ( *__receptor_type )[ "PRED_SPIKES_11" ] = 212,
    ( *__receptor_type )[ "PRED_SPIKES_12" ] = 213,
    ( *__receptor_type )[ "PRED_SPIKES_13" ] = 214,
    ( *__receptor_type )[ "PRED_SPIKES_14" ] = 215,
    ( *__receptor_type )[ "PRED_SPIKES_15" ] = 216,
    ( *__receptor_type )[ "PRED_SPIKES_16" ] = 217,
    ( *__receptor_type )[ "PRED_SPIKES_17" ] = 218,
    ( *__receptor_type )[ "PRED_SPIKES_18" ] = 219,
    ( *__receptor_type )[ "PRED_SPIKES_19" ] = 220,
    ( *__receptor_type )[ "PRED_SPIKES_20" ] = 221,
    ( *__receptor_type )[ "PRED_SPIKES_21" ] = 222,
    ( *__receptor_type )[ "PRED_SPIKES_22" ] = 223,
    ( *__receptor_type )[ "PRED_SPIKES_23" ] = 224,
    ( *__receptor_type )[ "PRED_SPIKES_24" ] = 225,
    ( *__receptor_type )[ "PRED_SPIKES_25" ] = 226,
    ( *__receptor_type )[ "PRED_SPIKES_26" ] = 227,
    ( *__receptor_type )[ "PRED_SPIKES_27" ] = 228,
    ( *__receptor_type )[ "PRED_SPIKES_28" ] = 229,
    ( *__receptor_type )[ "PRED_SPIKES_29" ] = 230,
    ( *__receptor_type )[ "PRED_SPIKES_30" ] = 231,
    ( *__receptor_type )[ "PRED_SPIKES_31" ] = 232,
    ( *__receptor_type )[ "PRED_SPIKES_32" ] = 233,
    ( *__receptor_type )[ "PRED_SPIKES_33" ] = 234,
    ( *__receptor_type )[ "PRED_SPIKES_34" ] = 235,
    ( *__receptor_type )[ "PRED_SPIKES_35" ] = 236,
    ( *__receptor_type )[ "PRED_SPIKES_36" ] = 237,
    ( *__receptor_type )[ "PRED_SPIKES_37" ] = 238,
    ( *__receptor_type )[ "PRED_SPIKES_38" ] = 239,
    ( *__receptor_type )[ "PRED_SPIKES_39" ] = 240,
    ( *__receptor_type )[ "PRED_SPIKES_40" ] = 241,
    ( *__receptor_type )[ "PRED_SPIKES_41" ] = 242,
    ( *__receptor_type )[ "PRED_SPIKES_42" ] = 243,
    ( *__receptor_type )[ "PRED_SPIKES_43" ] = 244,
    ( *__receptor_type )[ "PRED_SPIKES_44" ] = 245,
    ( *__receptor_type )[ "PRED_SPIKES_45" ] = 246,
    ( *__receptor_type )[ "PRED_SPIKES_46" ] = 247,
    ( *__receptor_type )[ "PRED_SPIKES_47" ] = 248,
    ( *__receptor_type )[ "PRED_SPIKES_48" ] = 249,
    ( *__receptor_type )[ "PRED_SPIKES_49" ] = 250,
    ( *__receptor_type )[ "PRED_SPIKES_50" ] = 251,
    ( *__receptor_type )[ "PRED_SPIKES_51" ] = 252,
    ( *__receptor_type )[ "PRED_SPIKES_52" ] = 253,
    ( *__receptor_type )[ "PRED_SPIKES_53" ] = 254,
    ( *__receptor_type )[ "PRED_SPIKES_54" ] = 255,
    ( *__receptor_type )[ "PRED_SPIKES_55" ] = 256,
    ( *__receptor_type )[ "PRED_SPIKES_56" ] = 257,
    ( *__receptor_type )[ "PRED_SPIKES_57" ] = 258,
    ( *__receptor_type )[ "PRED_SPIKES_58" ] = 259,
    ( *__receptor_type )[ "PRED_SPIKES_59" ] = 260,
    ( *__receptor_type )[ "PRED_SPIKES_60" ] = 261,
    ( *__receptor_type )[ "PRED_SPIKES_61" ] = 262,
    ( *__receptor_type )[ "PRED_SPIKES_62" ] = 263,
    ( *__receptor_type )[ "PRED_SPIKES_63" ] = 264,
    ( *__receptor_type )[ "PRED_SPIKES_64" ] = 265,
    ( *__receptor_type )[ "PRED_SPIKES_65" ] = 266,
    ( *__receptor_type )[ "PRED_SPIKES_66" ] = 267,
    ( *__receptor_type )[ "PRED_SPIKES_67" ] = 268,
    ( *__receptor_type )[ "PRED_SPIKES_68" ] = 269,
    ( *__receptor_type )[ "PRED_SPIKES_69" ] = 270,
    ( *__receptor_type )[ "PRED_SPIKES_70" ] = 271,
    ( *__receptor_type )[ "PRED_SPIKES_71" ] = 272,
    ( *__receptor_type )[ "PRED_SPIKES_72" ] = 273,
    ( *__receptor_type )[ "PRED_SPIKES_73" ] = 274,
    ( *__receptor_type )[ "PRED_SPIKES_74" ] = 275,
    ( *__receptor_type )[ "PRED_SPIKES_75" ] = 276,
    ( *__receptor_type )[ "PRED_SPIKES_76" ] = 277,
    ( *__receptor_type )[ "PRED_SPIKES_77" ] = 278,
    ( *__receptor_type )[ "PRED_SPIKES_78" ] = 279,
    ( *__receptor_type )[ "PRED_SPIKES_79" ] = 280,
    ( *__receptor_type )[ "PRED_SPIKES_80" ] = 281,
    ( *__receptor_type )[ "PRED_SPIKES_81" ] = 282,
    ( *__receptor_type )[ "PRED_SPIKES_82" ] = 283,
    ( *__receptor_type )[ "PRED_SPIKES_83" ] = 284,
    ( *__receptor_type )[ "PRED_SPIKES_84" ] = 285,
    ( *__receptor_type )[ "PRED_SPIKES_85" ] = 286,
    ( *__receptor_type )[ "PRED_SPIKES_86" ] = 287,
    ( *__receptor_type )[ "PRED_SPIKES_87" ] = 288,
    ( *__receptor_type )[ "PRED_SPIKES_88" ] = 289,
    ( *__receptor_type )[ "PRED_SPIKES_89" ] = 290,
    ( *__receptor_type )[ "PRED_SPIKES_90" ] = 291,
    ( *__receptor_type )[ "PRED_SPIKES_91" ] = 292,
    ( *__receptor_type )[ "PRED_SPIKES_92" ] = 293,
    ( *__receptor_type )[ "PRED_SPIKES_93" ] = 294,
    ( *__receptor_type )[ "PRED_SPIKES_94" ] = 295,
    ( *__receptor_type )[ "PRED_SPIKES_95" ] = 296,
    ( *__receptor_type )[ "PRED_SPIKES_96" ] = 297,
    ( *__receptor_type )[ "PRED_SPIKES_97" ] = 298,
    ( *__receptor_type )[ "PRED_SPIKES_98" ] = 299,
    ( *__receptor_type )[ "PRED_SPIKES_99" ] = 300,
    ( *__receptor_type )[ "PRED_SPIKES_100" ] = 301,
    ( *__receptor_type )[ "PRED_SPIKES_101" ] = 302,
    ( *__receptor_type )[ "PRED_SPIKES_102" ] = 303,
    ( *__receptor_type )[ "PRED_SPIKES_103" ] = 304,
    ( *__receptor_type )[ "PRED_SPIKES_104" ] = 305,
    ( *__receptor_type )[ "PRED_SPIKES_105" ] = 306,
    ( *__receptor_type )[ "PRED_SPIKES_106" ] = 307,
    ( *__receptor_type )[ "PRED_SPIKES_107" ] = 308,
    ( *__receptor_type )[ "PRED_SPIKES_108" ] = 309,
    ( *__receptor_type )[ "PRED_SPIKES_109" ] = 310,
    ( *__receptor_type )[ "PRED_SPIKES_110" ] = 311,
    ( *__receptor_type )[ "PRED_SPIKES_111" ] = 312,
    ( *__receptor_type )[ "PRED_SPIKES_112" ] = 313,
    ( *__receptor_type )[ "PRED_SPIKES_113" ] = 314,
    ( *__receptor_type )[ "PRED_SPIKES_114" ] = 315,
    ( *__receptor_type )[ "PRED_SPIKES_115" ] = 316,
    ( *__receptor_type )[ "PRED_SPIKES_116" ] = 317,
    ( *__receptor_type )[ "PRED_SPIKES_117" ] = 318,
    ( *__receptor_type )[ "PRED_SPIKES_118" ] = 319,
    ( *__receptor_type )[ "PRED_SPIKES_119" ] = 320,
    ( *__receptor_type )[ "PRED_SPIKES_120" ] = 321,
    ( *__receptor_type )[ "PRED_SPIKES_121" ] = 322,
    ( *__receptor_type )[ "PRED_SPIKES_122" ] = 323,
    ( *__receptor_type )[ "PRED_SPIKES_123" ] = 324,
    ( *__receptor_type )[ "PRED_SPIKES_124" ] = 325,
    ( *__receptor_type )[ "PRED_SPIKES_125" ] = 326,
    ( *__receptor_type )[ "PRED_SPIKES_126" ] = 327,
    ( *__receptor_type )[ "PRED_SPIKES_127" ] = 328,
    ( *__receptor_type )[ "PRED_SPIKES_128" ] = 329,
    ( *__receptor_type )[ "PRED_SPIKES_129" ] = 330,
    ( *__receptor_type )[ "PRED_SPIKES_130" ] = 331,
    ( *__receptor_type )[ "PRED_SPIKES_131" ] = 332,
    ( *__receptor_type )[ "PRED_SPIKES_132" ] = 333,
    ( *__receptor_type )[ "PRED_SPIKES_133" ] = 334,
    ( *__receptor_type )[ "PRED_SPIKES_134" ] = 335,
    ( *__receptor_type )[ "PRED_SPIKES_135" ] = 336,
    ( *__receptor_type )[ "PRED_SPIKES_136" ] = 337,
    ( *__receptor_type )[ "PRED_SPIKES_137" ] = 338,
    ( *__receptor_type )[ "PRED_SPIKES_138" ] = 339,
    ( *__receptor_type )[ "PRED_SPIKES_139" ] = 340,
    ( *__receptor_type )[ "PRED_SPIKES_140" ] = 341,
    ( *__receptor_type )[ "PRED_SPIKES_141" ] = 342,
    ( *__receptor_type )[ "PRED_SPIKES_142" ] = 343,
    ( *__receptor_type )[ "PRED_SPIKES_143" ] = 344,
    ( *__receptor_type )[ "PRED_SPIKES_144" ] = 345,
    ( *__receptor_type )[ "PRED_SPIKES_145" ] = 346,
    ( *__receptor_type )[ "PRED_SPIKES_146" ] = 347,
    ( *__receptor_type )[ "PRED_SPIKES_147" ] = 348,
    ( *__receptor_type )[ "PRED_SPIKES_148" ] = 349,
    ( *__receptor_type )[ "PRED_SPIKES_149" ] = 350,
    ( *__receptor_type )[ "PRED_SPIKES_150" ] = 351,
    ( *__receptor_type )[ "PRED_SPIKES_151" ] = 352,
    ( *__receptor_type )[ "PRED_SPIKES_152" ] = 353,
    ( *__receptor_type )[ "PRED_SPIKES_153" ] = 354,
    ( *__receptor_type )[ "PRED_SPIKES_154" ] = 355,
    ( *__receptor_type )[ "PRED_SPIKES_155" ] = 356,
    ( *__receptor_type )[ "PRED_SPIKES_156" ] = 357,
    ( *__receptor_type )[ "PRED_SPIKES_157" ] = 358,
    ( *__receptor_type )[ "PRED_SPIKES_158" ] = 359,
    ( *__receptor_type )[ "PRED_SPIKES_159" ] = 360,
    ( *__receptor_type )[ "PRED_SPIKES_160" ] = 361,
    ( *__receptor_type )[ "PRED_SPIKES_161" ] = 362,
    ( *__receptor_type )[ "PRED_SPIKES_162" ] = 363,
    ( *__receptor_type )[ "PRED_SPIKES_163" ] = 364,
    ( *__receptor_type )[ "PRED_SPIKES_164" ] = 365,
    ( *__receptor_type )[ "PRED_SPIKES_165" ] = 366,
    ( *__receptor_type )[ "PRED_SPIKES_166" ] = 367,
    ( *__receptor_type )[ "PRED_SPIKES_167" ] = 368,
    ( *__receptor_type )[ "PRED_SPIKES_168" ] = 369,
    ( *__receptor_type )[ "PRED_SPIKES_169" ] = 370,
    ( *__receptor_type )[ "PRED_SPIKES_170" ] = 371,
    ( *__receptor_type )[ "PRED_SPIKES_171" ] = 372,
    ( *__receptor_type )[ "PRED_SPIKES_172" ] = 373,
    ( *__receptor_type )[ "PRED_SPIKES_173" ] = 374,
    ( *__receptor_type )[ "PRED_SPIKES_174" ] = 375,
    ( *__receptor_type )[ "PRED_SPIKES_175" ] = 376,
    ( *__receptor_type )[ "PRED_SPIKES_176" ] = 377,
    ( *__receptor_type )[ "PRED_SPIKES_177" ] = 378,
    ( *__receptor_type )[ "PRED_SPIKES_178" ] = 379,
    ( *__receptor_type )[ "PRED_SPIKES_179" ] = 380,
    ( *__receptor_type )[ "PRED_SPIKES_180" ] = 381,
    ( *__receptor_type )[ "PRED_SPIKES_181" ] = 382,
    ( *__receptor_type )[ "PRED_SPIKES_182" ] = 383,
    ( *__receptor_type )[ "PRED_SPIKES_183" ] = 384,
    ( *__receptor_type )[ "PRED_SPIKES_184" ] = 385,
    ( *__receptor_type )[ "PRED_SPIKES_185" ] = 386,
    ( *__receptor_type )[ "PRED_SPIKES_186" ] = 387,
    ( *__receptor_type )[ "PRED_SPIKES_187" ] = 388,
    ( *__receptor_type )[ "PRED_SPIKES_188" ] = 389,
    ( *__receptor_type )[ "PRED_SPIKES_189" ] = 390,
    ( *__receptor_type )[ "PRED_SPIKES_190" ] = 391,
    ( *__receptor_type )[ "PRED_SPIKES_191" ] = 392,
    ( *__receptor_type )[ "PRED_SPIKES_192" ] = 393,
    ( *__receptor_type )[ "PRED_SPIKES_193" ] = 394,
    ( *__receptor_type )[ "PRED_SPIKES_194" ] = 395,
    ( *__receptor_type )[ "PRED_SPIKES_195" ] = 396,
    ( *__receptor_type )[ "PRED_SPIKES_196" ] = 397,
    ( *__receptor_type )[ "PRED_SPIKES_197" ] = 398,
    ( *__receptor_type )[ "PRED_SPIKES_198" ] = 399,
    ( *__receptor_type )[ "PRED_SPIKES_199" ] = 400,
    ( *__receptor_type )[ "ERROR_SPIKES" ] = 401;
    ( *__d )[ "receptor_types" ] = __receptor_type;

  (*__d)[nest::names::recordables] = recordablesMap_.get_list();
}

inline void state_neuron::set_status(const DictionaryDatum &__d)
{
  // parameters
  double tmp_kp = get_kp();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_kp, tmp_kp, this);
  // Resize vectors
  if (tmp_kp != get_kp())
  {
  }
  bool tmp_pos = get_pos();
  nest::updateValueParam<bool>(__d, nest::state_neuron_names::_pos, tmp_pos, this);
  // Resize vectors
  if (tmp_pos != get_pos())
  {
  }
  double tmp_base_rate = get_base_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_base_rate, tmp_base_rate, this);
  // Resize vectors
  if (tmp_base_rate != get_base_rate())
  {
  }
  double tmp_buffer_size = get_buffer_size();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_buffer_size, tmp_buffer_size, this);
  // Resize vectors
  if (tmp_buffer_size != get_buffer_size())
  {
  }
  double tmp_buffer_size_error = get_buffer_size_error();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_buffer_size_error, tmp_buffer_size_error, this);
  // Resize vectors
  if (tmp_buffer_size_error != get_buffer_size_error())
  {
  }
  long tmp_simulation_steps = get_simulation_steps();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_simulation_steps, tmp_simulation_steps, this);
  // Resize vectors
  if (tmp_simulation_steps != get_simulation_steps())
  {
  }
  long tmp_N_fbk = get_N_fbk();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_N_fbk, tmp_N_fbk, this);
  // Resize vectors
  if (tmp_N_fbk != get_N_fbk())
  {
    std::vector< double >  _tmp_current_fbk_input = get_current_fbk_input();
    _tmp_current_fbk_input.resize(tmp_N_fbk, 0.);
    set_current_fbk_input(_tmp_current_fbk_input);
    std::vector< double >  _tmp_fbk_counts = get_fbk_counts();
    _tmp_fbk_counts.resize(tmp_N_fbk, 0.);
    set_fbk_counts(_tmp_fbk_counts);
  }
  long tmp_N_pred = get_N_pred();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_N_pred, tmp_N_pred, this);
  // Resize vectors
  if (tmp_N_pred != get_N_pred())
  {
    std::vector< double >  _tmp_current_pred_input = get_current_pred_input();
    _tmp_current_pred_input.resize(tmp_N_pred, 0.);
    set_current_pred_input(_tmp_current_pred_input);
    std::vector< double >  _tmp_pred_counts = get_pred_counts();
    _tmp_pred_counts.resize(tmp_N_pred, 0.);
    set_pred_counts(_tmp_pred_counts);
  }
  long tmp_N_error = get_N_error();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_N_error, tmp_N_error, this);
  // Resize vectors
  if (tmp_N_error != get_N_error())
  {
  }
  double tmp_C_error = get_C_error();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_C_error, tmp_C_error, this);
  // Resize vectors
  if (tmp_C_error != get_C_error())
  {
  }
  long tmp_fbk_bf_size = get_fbk_bf_size();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_fbk_bf_size, tmp_fbk_bf_size, this);
  // Resize vectors
  if (tmp_fbk_bf_size != get_fbk_bf_size())
  {
    std::vector< double >  _tmp_fbk_buffer = get_fbk_buffer();
    _tmp_fbk_buffer.resize(tmp_fbk_bf_size, 0.);
    set_fbk_buffer(_tmp_fbk_buffer);
  }
  long tmp_pred_bf_size = get_pred_bf_size();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_pred_bf_size, tmp_pred_bf_size, this);
  // Resize vectors
  if (tmp_pred_bf_size != get_pred_bf_size())
  {
    std::vector< double >  _tmp_pred_buffer = get_pred_buffer();
    _tmp_pred_buffer.resize(tmp_pred_bf_size, 0.);
    set_pred_buffer(_tmp_pred_buffer);
  }
  long tmp_error_bf_size = get_error_bf_size();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_error_bf_size, tmp_error_bf_size, this);
  // Resize vectors
  if (tmp_error_bf_size != get_error_bf_size())
  {
    std::vector< double >  _tmp_error_buffer = get_error_buffer();
    _tmp_error_buffer.resize(tmp_error_bf_size, 0.);
    set_error_buffer(_tmp_error_buffer);
  }
  double tmp_time_wait = get_time_wait();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_time_wait, tmp_time_wait, this);
  // Resize vectors
  if (tmp_time_wait != get_time_wait())
  {
  }
  double tmp_time_trial = get_time_trial();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_time_trial, tmp_time_trial, this);
  // Resize vectors
  if (tmp_time_trial != get_time_trial())
  {
  }

  // initial values for state variables in ODE or kernel
  double tmp_in_rate = get_in_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_in_rate, tmp_in_rate, this);
  double tmp_out_rate = get_out_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_out_rate, tmp_out_rate, this);
  long tmp_spike_count_out = get_spike_count_out();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_spike_count_out, tmp_spike_count_out, this);
  std::vector< double >  tmp_current_fbk_input = get_current_fbk_input();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_current_fbk_input, tmp_current_fbk_input);
   
  // Check if the new vector size matches its original size
  if ( tmp_current_fbk_input.size() != tmp_N_fbk )
  {
    std::stringstream msg;
    msg << "The vector \"current_fbk_input\" does not match its size: " << tmp_N_fbk;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_current_pred_input = get_current_pred_input();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_current_pred_input, tmp_current_pred_input);
   
  // Check if the new vector size matches its original size
  if ( tmp_current_pred_input.size() != tmp_N_pred )
  {
    std::stringstream msg;
    msg << "The vector \"current_pred_input\" does not match its size: " << tmp_N_pred;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_fbk_buffer = get_fbk_buffer();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_fbk_buffer, tmp_fbk_buffer);
   
  // Check if the new vector size matches its original size
  if ( tmp_fbk_buffer.size() != tmp_fbk_bf_size )
  {
    std::stringstream msg;
    msg << "The vector \"fbk_buffer\" does not match its size: " << tmp_fbk_bf_size;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_pred_buffer = get_pred_buffer();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_pred_buffer, tmp_pred_buffer);
   
  // Check if the new vector size matches its original size
  if ( tmp_pred_buffer.size() != tmp_pred_bf_size )
  {
    std::stringstream msg;
    msg << "The vector \"pred_buffer\" does not match its size: " << tmp_pred_bf_size;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_fbk_counts = get_fbk_counts();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_fbk_counts, tmp_fbk_counts);
   
  // Check if the new vector size matches its original size
  if ( tmp_fbk_counts.size() != tmp_N_fbk )
  {
    std::stringstream msg;
    msg << "The vector \"fbk_counts\" does not match its size: " << tmp_N_fbk;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_pred_counts = get_pred_counts();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_pred_counts, tmp_pred_counts);
   
  // Check if the new vector size matches its original size
  if ( tmp_pred_counts.size() != tmp_N_pred )
  {
    std::stringstream msg;
    msg << "The vector \"pred_counts\" does not match its size: " << tmp_N_pred;
    throw nest::BadProperty(msg.str());
  }
  long tmp_tick = get_tick();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_tick, tmp_tick, this);
  long tmp_position_count = get_position_count();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_position_count, tmp_position_count, this);
  double tmp_mean_fbk = get_mean_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_mean_fbk, tmp_mean_fbk, this);
  double tmp_mean_pred = get_mean_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_mean_pred, tmp_mean_pred, this);
  double tmp_var_fbk = get_var_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_var_fbk, tmp_var_fbk, this);
  double tmp_var_pred = get_var_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_var_pred, tmp_var_pred, this);
  double tmp_CV_fbk = get_CV_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_CV_fbk, tmp_CV_fbk, this);
  double tmp_CV_pred = get_CV_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_CV_pred, tmp_CV_pred, this);
  double tmp_current_error_input = get_current_error_input();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_current_error_input, tmp_current_error_input, this);
  std::vector< double >  tmp_error_buffer = get_error_buffer();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_error_buffer, tmp_error_buffer);
   
  // Check if the new vector size matches its original size
  if ( tmp_error_buffer.size() != tmp_error_bf_size )
  {
    std::stringstream msg;
    msg << "The vector \"error_buffer\" does not match its size: " << tmp_error_bf_size;
    throw nest::BadProperty(msg.str());
  }
  long tmp_err_pos_count = get_err_pos_count();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_err_pos_count, tmp_err_pos_count, this);
  double tmp_error_counts = get_error_counts();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_error_counts, tmp_error_counts, this);
  double tmp_error_rate = get_error_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_error_rate, tmp_error_rate, this);
  double tmp_fbk_rate = get_fbk_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_fbk_rate, tmp_fbk_rate, this);
  double tmp_w_fbk = get_w_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_w_fbk, tmp_w_fbk, this);
  double tmp_w_pred = get_w_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_w_pred, tmp_w_pred, this);
  double tmp_total_CV = get_total_CV();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_total_CV, tmp_total_CV, this);
  double tmp_lambda_poisson = get_lambda_poisson();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_lambda_poisson, tmp_lambda_poisson, this);

  // We now know that (ptmp, stmp) are consistent. We do not
  // write them back to (P_, S_) before we are also sure that
  // the properties to be set in the parent class are internally
  // consistent.
  ArchivingNode::set_status(__d);

  // if we get here, temporaries contain consistent set of properties
  set_kp(tmp_kp);
  set_pos(tmp_pos);
  set_base_rate(tmp_base_rate);
  set_buffer_size(tmp_buffer_size);
  set_buffer_size_error(tmp_buffer_size_error);
  set_simulation_steps(tmp_simulation_steps);
  set_N_fbk(tmp_N_fbk);
  set_N_pred(tmp_N_pred);
  set_N_error(tmp_N_error);
  set_C_error(tmp_C_error);
  set_fbk_bf_size(tmp_fbk_bf_size);
  set_pred_bf_size(tmp_pred_bf_size);
  set_error_bf_size(tmp_error_bf_size);
  set_time_wait(tmp_time_wait);
  set_time_trial(tmp_time_trial);
  set_in_rate(tmp_in_rate);
  set_out_rate(tmp_out_rate);
  set_spike_count_out(tmp_spike_count_out);
  set_current_fbk_input(tmp_current_fbk_input);
  set_current_pred_input(tmp_current_pred_input);
  set_fbk_buffer(tmp_fbk_buffer);
  set_pred_buffer(tmp_pred_buffer);
  set_fbk_counts(tmp_fbk_counts);
  set_pred_counts(tmp_pred_counts);
  set_tick(tmp_tick);
  set_position_count(tmp_position_count);
  set_mean_fbk(tmp_mean_fbk);
  set_mean_pred(tmp_mean_pred);
  set_var_fbk(tmp_var_fbk);
  set_var_pred(tmp_var_pred);
  set_CV_fbk(tmp_CV_fbk);
  set_CV_pred(tmp_CV_pred);
  set_current_error_input(tmp_current_error_input);
  set_error_buffer(tmp_error_buffer);
  set_err_pos_count(tmp_err_pos_count);
  set_error_counts(tmp_error_counts);
  set_error_rate(tmp_error_rate);
  set_fbk_rate(tmp_fbk_rate);
  set_w_fbk(tmp_w_fbk);
  set_w_pred(tmp_w_pred);
  set_total_CV(tmp_total_CV);
  set_lambda_poisson(tmp_lambda_poisson);





  // recompute internal variables in case they are dependent on parameters or state that might have been updated in this call to set_status()
  recompute_internal_variables();
};



#endif /* #ifndef STATE_NEURON */
