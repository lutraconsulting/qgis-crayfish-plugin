/* A Bison parser, made by GNU Bison 3.0.4.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015 Free Software Foundation, Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

#ifndef YY_MESH_BISON_CRAYFISH_MESH_CALCULATOR_PARSER_HPP_INCLUDED
# define YY_MESH_BISON_CRAYFISH_MESH_CALCULATOR_PARSER_HPP_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 1
#endif
#if YYDEBUG
extern int meshdebug;
#endif

/* Token type.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    NODATA = 258,
    DATASET_REF = 259,
    NUMBER = 260,
    FUNCTION = 261,
    FUNCTION2 = 262,
    AND = 263,
    OR = 264,
    NOT = 265,
    NE = 266,
    GE = 267,
    LE = 268,
    IF = 269,
    UMINUS = 270
  };
#endif

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED

union YYSTYPE
{
#line 60 "crayfish_mesh_calculator_parser.yy" /* yacc.c:1909  */
 CrayfishMeshCalculatorNode* node; double number; CrayfishMeshCalculatorNode::Operator op;

#line 73 "bison_crayfish_mesh_calculator_parser.hpp" /* yacc.c:1909  */
};

typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE meshlval;

int meshparse (void);

#endif /* !YY_MESH_BISON_CRAYFISH_MESH_CALCULATOR_PARSER_HPP_INCLUDED  */
