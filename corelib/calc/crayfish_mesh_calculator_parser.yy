/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2017 Lutra Consulting

info at lutraconsulting dot co dot uk
Lutra Consulting
23 Chestnut Close
Burgess Hill
West Sussex
RH15 8HN

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

%{
  #include "calc/crayfish_mesh_calculator_node.h"

#ifdef _MSC_VER
#  pragma warning( disable: 4065 )  // switch statement contains 'default' but no 'case' labels
#  pragma warning( disable: 4701 )  // Potentially uninitialized local variable 'name' used
#endif

  // don't redeclare malloc/free
  #define YYINCLUDED_STDLIB_H 1

  CrayfishMeshCalculatorNode* parseMeshCalcString(const QString& str, QString& parserErrorMsg);

  //! from lex.yy.c
  extern int meshlex();
  extern char* meshtext;
  extern void set_mesh_input_buffer(const char* buffer);

  //! varible where the parser error will be stored
  QString rParserErrorMsg;

  //! sets gParserErrorMsg
  void mesherror(const char* msg);

  //! temporary list for nodes without parent (if parsing fails these nodes are removed)
  QList<CrayfishMeshCalculatorNode*> gTmpNodes;
  void joinTmpNodes(CrayfishMeshCalculatorNode* parent, CrayfishMeshCalculatorNode* left, CrayfishMeshCalculatorNode* right);
  void addToTmpNodes(CrayfishMeshCalculatorNode* node);

  // we want verbose error messages
  #define YYERROR_VERBOSE 1
%}

%union { CrayfishMeshCalculatorNode* node; double number; CrayfishMeshCalculatorNode::Operator op;}

%start root

%token DATASET_REF
%token<number> NUMBER
%token<op> FUNCTION

%type <node> root
%type <node> mesh_exp

%left AND
%left OR
%left NE
%left GE
%left LE

%left '=' '<' '>'
%left '+' '-'
%left '*' '/'
%left '^'
%left UMINUS  // fictitious symbol (for unary minus)

%%

root: mesh_exp{}
;

mesh_exp:
  FUNCTION '(' mesh_exp ')'   { $$ = new CrayfishMeshCalculatorNode($1, $3, 0); joinTmpNodes($$, $3, 0);}
  | mesh_exp AND mesh_exp     { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opAND, $1, $3 ); joinTmpNodes($$,$1,$3); }
  | mesh_exp OR mesh_exp      { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opOR, $1, $3 ); joinTmpNodes($$,$1,$3); }
  | mesh_exp '=' mesh_exp     { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opEQ, $1, $3 ); joinTmpNodes($$,$1,$3); }
  | mesh_exp NE mesh_exp      { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opNE, $1, $3 ); joinTmpNodes($$,$1,$3); }
  | mesh_exp '>' mesh_exp     { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opGT, $1, $3 ); joinTmpNodes($$, $1, $3); }
  | mesh_exp '<' mesh_exp     { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opLT, $1, $3 ); joinTmpNodes($$, $1, $3); }
  | mesh_exp GE mesh_exp      { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opGE, $1, $3 ); joinTmpNodes($$, $1, $3); }
  | mesh_exp LE mesh_exp      { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opLE, $1, $3 ); joinTmpNodes($$, $1, $3); }
  | mesh_exp '^' mesh_exp     { $$ = new CrayfishMeshCalculatorNode(CrayfishMeshCalculatorNode::opPOW, $1, $3); joinTmpNodes($$,$1,$3); }
  | mesh_exp '*' mesh_exp     { $$ = new CrayfishMeshCalculatorNode(CrayfishMeshCalculatorNode::opMUL, $1, $3); joinTmpNodes($$,$1,$3); }
  | mesh_exp '/' mesh_exp     { $$ = new CrayfishMeshCalculatorNode(CrayfishMeshCalculatorNode::opDIV, $1, $3); joinTmpNodes($$,$1,$3); }
  | mesh_exp '+' mesh_exp     { $$ = new CrayfishMeshCalculatorNode(CrayfishMeshCalculatorNode::opPLUS, $1, $3); joinTmpNodes($$,$1,$3); }
  | mesh_exp '-' mesh_exp     { $$ = new CrayfishMeshCalculatorNode(CrayfishMeshCalculatorNode::opMINUS, $1, $3); joinTmpNodes($$,$1,$3); }
  | '(' mesh_exp ')'          { $$ = $2; }
  | '+' mesh_exp %prec UMINUS { $$ = $2; }
  | '-' mesh_exp %prec UMINUS { $$ = new CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode::opSIGN, $2, 0 ); joinTmpNodes($$, $2, 0); }
  | NUMBER { $$ = new CrayfishMeshCalculatorNode($1); addToTmpNodes($$); }
  | DATASET_REF { $$ = new CrayfishMeshCalculatorNode(QString::fromUtf8(meshtext)); addToTmpNodes($$); }
;

%%

void addToTmpNodes(CrayfishMeshCalculatorNode* node)
{
  gTmpNodes.append(node);
}


void joinTmpNodes(CrayfishMeshCalculatorNode* parent, CrayfishMeshCalculatorNode* left, CrayfishMeshCalculatorNode* right)
{
  bool res;
  Q_UNUSED(res);

  if (left)
  {
    res = gTmpNodes.removeAll(left) != 0;
    Q_ASSERT(res);
  }

  if (right)
  {
    res = gTmpNodes.removeAll(right) != 0;
    Q_ASSERT(res);
  }

  gTmpNodes.append(parent);
}


CrayfishMeshCalculatorNode* localParseMeshCalcString(const QString& str, QString& parserErrorMsg)
{
  // list should be empty when starting
  Q_ASSERT(gTmpNodes.count() == 0);

  set_mesh_input_buffer(str.toUtf8().constData());
  int res = meshparse();

  // list should be empty when parsing was OK
  if (res == 0) // success?
  {
    Q_ASSERT(gTmpNodes.count() == 1);
    return gTmpNodes.takeFirst();
  }
  else // error?
  {
    parserErrorMsg = rParserErrorMsg;
    // remove nodes without parents - to prevent memory leaks
    while (gTmpNodes.size() > 0)
      delete gTmpNodes.takeFirst();
    return nullptr;
  }
}

void mesherror(const char* msg)
{
  rParserErrorMsg = msg;
}



